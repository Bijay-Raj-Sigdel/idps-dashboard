import random
from datetime import datetime
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app import schemas
from app.db import get_db
from app.db_models import PredictionLog
from app.model import model_handler
from app.schemas import PredictionRequest, PredictionResponse

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
    """Run real-time inference on a set of network flow features."""
    try:
        feature_dict = payload.model_dump(by_alias=True)
        result = model_handler.predict(feature_dict)

        # Unaltered ML model output
        predicted_label = str(result["prediction"])

        # Simulator ground truth
        ground_truth = feature_dict.get("attack_type", None)
        data_source = feature_dict.get("data_source", "CICIDS2017")

        # Generate integer prediction_id upfront
        gen_prediction_id = random.randint(1, 2_000_000_000)

        # Log to Database
        log_entry = PredictionLog(
            prediction_id=gen_prediction_id,
            input_features=feature_dict,
            predicted_label=predicted_label,
            ground_truth_label=ground_truth,
            data_source=data_source,
            confidence=result["confidence"],
            probabilities=result["probabilities"],
        )

        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        result["prediction_id"] = log_entry.prediction_id
        return result

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/logs", response_model=List[schemas.PredictionLogOut])
def get_logs(
    limit: int = Query(default=20, le=100),
    attack_type: Optional[str] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Fetch recent prediction logs with real-time dynamic filtering."""
    query = db.query(PredictionLog)

    # 1. Filter by Attack/Classification Type if specified
    if attack_type and attack_type.strip() != "":
        query = query.filter(
            func.lower(PredictionLog.predicted_label)
            == attack_type.lower().strip()
        )

    # 2. Filter by Start Date/Time if specified
    if start_date and start_date.strip() != "":
        try:
            parsed_date = datetime.fromisoformat(start_date)
            query = query.filter(PredictionLog.timestamp >= parsed_date)
        except ValueError:
            pass  # Ignore invalid date formats gracefully

    logs = query.order_by(PredictionLog.id.desc()).limit(limit).all()
    return logs


@router.get("/stats/summary", response_model=schemas.StatsSummaryResponse)
def get_stats_summary(db: Session = Depends(get_db)):
    """Aggregate statistics for Recharts dashboard graphs."""
    total_inspected = db.query(func.count(PredictionLog.id)).scalar() or 0
    benign_count = (
        db.query(func.count(PredictionLog.id))
        .filter(PredictionLog.predicted_label == "BENIGN")
        .scalar()
        or 0
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
    time_bucket = func.date_trunc("minute", PredictionLog.timestamp)
    volume_rows = (
        db.query(
            time_bucket.label("bucket"),
            func.count(PredictionLog.id).label("count"),
            func.sum(
                case((PredictionLog.predicted_label != "BENIGN", 1), else_=0)
            ).label("threats"),
        )
        .group_by(time_bucket)
        .order_by(time_bucket.desc())
        .limit(30)
        .all()
    )
    volume_rows = list(
        reversed(volume_rows)
    )  # chronological order for the chart

    volume_over_time = [
        {
            "time": bucket.strftime("%H:%M") if bucket else "--:--",
            "count": count,
            "threats": int(threats or 0),
        }
        for bucket, count, threats in volume_rows
    ]

    return {
        "total_inspected": total_inspected,
        "benign_count": benign_count,
        "threat_count": threat_count,
        "avg_confidence": round(float(avg_conf), 2),
        "label_distribution": label_distribution,
        "volume_over_time": volume_over_time,
    }


@router.get("/model/importance")
def get_feature_importance():
    """Fetch sorted feature importances from the loaded ML model."""
    if not hasattr(model_handler.model, "feature_importances_"):
        raise HTTPException(
            status_code=400,
            detail="Model does not support feature_importances_",
        )

    importances = model_handler.model.feature_importances_
    features_sorted = sorted(
        [
            {"feature": name, "importance": float(imp)}
            for name, imp in zip(model_handler.expected_features, importances)
        ],
        key=lambda x: x["importance"],
        reverse=True,
    )
    return {"status": "success", "data": features_sorted}

@router.get("/stats/accuracy")
def get_accuracy_stats(db: Session = Depends(get_db)):
    # Fetch logs with ground truth values
    logs = db.query(PredictionLog).filter(PredictionLog.ground_truth_label.isnot(None)).all()
    
    if not logs:
        return {"overall_accuracy": 0.0, "total_samples": 0, "per_class_accuracy": {}}
    
    total_samples = len(logs)
    correct_predictions = sum(1 for log in logs if log.predicted_label == log.ground_truth_label)
    overall_accuracy = round(correct_predictions / total_samples, 4)
    
    # Calculate per-class breakdown
    class_stats = {}
    for log in logs:
        gt = log.ground_truth_label
        if gt not in class_stats:
            class_stats[gt] = {"correct": 0, "total": 0}
        class_stats[gt]["total"] += 1
        if log.predicted_label == gt:
            class_stats[gt]["correct"] += 1
            
    per_class_acc = {
        cls: round(data["correct"] / data["total"], 4)
        for cls, data in class_stats.items()
    }
    
    return {
        "overall_accuracy": overall_accuracy,
        "total_samples": total_samples,
        "per_class_accuracy": per_class_acc
    }