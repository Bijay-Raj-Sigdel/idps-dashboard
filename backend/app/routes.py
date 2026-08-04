from fastapi import APIRouter, HTTPException, Depends, status

from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.db import get_db
from app.model import model_handler
from app.schemas import PredictionRequest, PredictionResponse

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint validating DB Connectivity and ML model availability."""
    db_ok = False
    try:
        db.execute(text("Select 1"))
        db_ok = True
    except Exception:
        db_ok = False

    model_loaded =(
        model_handler.model is not None
        and model_handler.label_encoder is not None
    )

    if not db_ok or not model_loaded:
        raise HTTPException(
            Status_code = status.HTTP_503_SERVICE_UNAVAILABLE,
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
def predict(payload: PredictionRequest):
    """Run real-time inference on a set of 15 network flow features."""
    try:
        feature_dict = payload.model_dump(by_alias=True)
        result = model_handler.predict(feature_dict)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )