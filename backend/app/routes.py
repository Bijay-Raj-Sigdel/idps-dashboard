from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from sqlalchemy import func, case
from typing import List

from app.db import get_db
from app.model import model_handler
from app.schemas import PredictionRequest, PredictionResponse
from app.db_models import PredictionLog
from app import schemas

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint validating DB Connectivity and ML model availability."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    model_loaded = (
        model_handler.model is not None
        and model_handler.label_encoder is not None
    )

    if not db_ok or not model_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "database_connected": db_ok,
                "model_loaded": model_loaded,
            },
        )

    return {
        "status": "healthy",
        "database_connected": db_ok,
        "model_loaded": model_loaded,
    }

@router.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest, db: Session = Depends(get_db)):
    """Run real-time inference on a set of 15 network flow features."""
    try:
        feature_dict = payload.model_dump(by_alias=True)
        result = model_handler.predict(feature_dict)

        # Pass prediction_id to satisfy DB NOT NULL constraint
        log_entry = PredictionLog(
            input_features=feature_dict,
            predicted_label=result["prediction"],
            confidence=result["confidence"],
            probabilities=result["probabilities"],
        )
        db.add(log_entry)
        db.flush()  # Populates log_entry.id without committing transaction yet

        log_entry.prediction_id = log_entry.id
        db.commit()
        db.refresh(log_entry)

        result["prediction_id"] = log_entry.id

        return result
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

@router.get("/logs", response_model=List[schemas.PredictionLogOut])
def get_logs(limit: int = Query(default=20, le=100), db: Session = Depends(get_db)):
    """Fetch recent prediction logs for the dashboard."""
    logs = db.query(PredictionLog).order_by(PredictionLog.id.desc()).limit(limit).all()
    return logs

# 4. Analytics Summary
@router.get("/stats/summary", response_model=schemas.StatsSummaryResponse)
def get_stats_summary(db: Session = Depends(get_db)):
    """Aggregate statistics for Recharts dashboard graphs."""
    total_inspected = db.query(func.count(PredictionLog.id)).scalar() or 0
    benign_count = (
        db.query(func.count(PredictionLog.id))
        .filter(PredictionLog.predicted_label == "BENIGN")
        .scalar() or 0
    )
    threat_count = total_inspected - benign_count
    avg_conf = db.query(func.avg(PredictionLog.confidence)).scalar() or 0.0

    # Group by label
    label_rows = (
        db.query(PredictionLog.predicted_label, func.count(PredictionLog.id))
        .group_by(PredictionLog.predicted_label)
        .all()
    )
    label_distribution = [
        {"label": label, "count": count} for label, count in label_rows
    ]

    # Group by minute bucket
    time_bucket = func.date_trunc('minute', PredictionLog.timestamp)
    volume_rows = (
        db.query(
            time_bucket.label("bucket"),
            func.count(PredictionLog.id).label("count"),
            func.sum(case((PredictionLog.predicted_label != "BENIGN", 1), else_=0)).label("threats")
        )
        .group_by(time_bucket)          
        .order_by(time_bucket.desc())    
        .limit(30)
        .all()
    )
    volume_rows = list(reversed(volume_rows)) # chronological order for the chart

    volume_over_time = [
        {
            "time": bucket.strftime("%H:%M") if bucket else "--:--",
            "count": count,
            "threats": int(threats or 0)
        }
        for bucket, count, threats in volume_rows
    ]

    return {
        "total_inspected": total_inspected,
        "benign_count": benign_count,
        "threat_count": threat_count,
        "avg_confidence": round(float(avg_conf) * 100, 2),
        "label_distribution": label_distribution,
        "volume_over_time": volume_over_time
    }