from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from typing import List

from app.db import get_db
from app.model import model_handler
from app.schemas import PredictionRequest, PredictionResponse
from app.db_models import PredictionLog

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
            prediction_id=result.get("prediction_id", 0),
            confidence=result["confidence"],
            probabilities=result["probabilities"],
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        # Update returned payload with auto-incremented DB ID
        result["prediction_id"] = log_entry.id

        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

@router.get("/logs")
def get_logs(limit: int = Query(default=20, le=100), db: Session = Depends(get_db)):
    """Fetch recent prediction logs for the dashboard."""
    logs = db.query(PredictionLog).order_by(PredictionLog.id.desc()).limit(limit).all()
    return logs