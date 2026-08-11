from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine, Base
import app.db_models
from app.routes import router

# Automatically create database tables if they do not exist
Base.metadata.create_all(bind=engine)

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

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)