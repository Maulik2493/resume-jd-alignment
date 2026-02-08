from pydantic import BaseModel
from typing import List

class ResumeInput(BaseModel):
    text: str

class JDInput(BaseModel):
    text: str

class AnalyzeRequest(BaseModel):
    resume: ResumeInput
    jd: JDInput

class CategoryASuggestion(BaseModel):
    type: str  # A1, A2, A3
    original: str
    suggestion: str
    justification: str

class CategoryBFeedback(BaseModel):
    gap: str
    justification: str

class AnalyzeResponse(BaseModel):
    category_a: List[CategoryASuggestion]
    category_b: List[CategoryBFeedback]
