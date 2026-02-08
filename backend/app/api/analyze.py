from fastapi import APIRouter
from app.models.schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter()

@router.post("/", response_model=AnalyzeResponse)
def analyze(data: AnalyzeRequest):
    # placeholder
    return AnalyzeResponse(
        category_a=[],
        category_b=[]
    )
