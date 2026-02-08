from fastapi import FastAPI
from app.api.analyze import router as analyze_router

app = FastAPI(title="Resume-JD Alignment Engine")

app.include_router(analyze_router, prefix="/analyze")
