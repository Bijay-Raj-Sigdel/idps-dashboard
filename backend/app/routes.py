from fastapi import APIRouter, HTTPException

from app.model import model_handler
from app.schemas import PredictionRequest, PredictionResponse

router = APIRouter()

@router.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest):
    feature_dict = payload.model_dump(by_alias=True)

    try: 
        result = model_handler.predict(feature_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, details=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

    return result