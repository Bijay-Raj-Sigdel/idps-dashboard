from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.schemas import PredictionRequest, PredictionResponse
from app.model import model_handler
from app.db import get_db

app = FastAPI(
    title="IDPS Threat Detection Engine API",
    description="Live inference API for network intrusion detection using trained ML models.",
    version="1.0.0"
)

# Enable CORS for future React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint that verifies API readiness, model state,
    and PostgreSQL connectivity.
    """
    try:
        # Execute quick DB connectivity probe
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"unreachable ({str(e)})"

    return {
        "status": "healthy",
        "database": db_status,
        "model_loaded": model_handler.model is not None,
        "expected_features": model_handler.feature_count
    }


@app.post("/predict", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
def predict_flow(request: PredictionRequest):
    """
    Accepts raw network flow features, validates them using Pydantic,
    executes model inference, and returns predicted threat class with confidence.
    """
    try:
        # Convert request to dict using aliases (e.g. "Destination Port")
        payload = request.model_dump(by_alias=True)
        
        # Execute model prediction
        result = model_handler.predict(payload)
        
        return PredictionResponse(**result)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference pipeline failed: {str(e)}"
        )



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)