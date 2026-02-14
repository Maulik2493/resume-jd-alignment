from fastapi import FastAPI
from app.api.analyze import router as analyze_router
from app.api.debug import router as debug_router

app = FastAPI(title="Resume-JD Alignment Engine")

app.include_router(analyze_router, prefix="/analyze")
app.include_router(debug_router, prefix="/debug", tags=["Debug"])
