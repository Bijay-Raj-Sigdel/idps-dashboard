from fastapi import FastAPI

from app.routes import router

app = FastAPI(title="IDPS Dashboard API")

app.include_router(router)