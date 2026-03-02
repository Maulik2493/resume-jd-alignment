"""Debug endpoints for testing pipeline stages in isolation.

These are development-only routes — not part of the production API.
They let you test the LLM service, resume parser, and JD parser
individually through Swagger UI.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models.schemas import ParsedResume, ParsedJobDescription
from app.services.llm import call_llm

router = APIRouter()


# ── Test LLM connectivity ──────────────────────────────────────────────────────


class LLMTestRequest(BaseModel):
    prompt: str = Field("I bought apples, bananas, and oranges.", description="Any text to process")


class LLMTestResponse(BaseModel):
    fruits: list[str] = Field(..., description="Fruits mentioned in the text")
    count: int = Field(..., description="Number of fruits found")


@router.post("/llm", response_model=LLMTestResponse, summary="Test LLM connectivity")
def test_llm(request: LLMTestRequest):
    """Verify API key works, structured output works, Pydantic validation works."""
    return call_llm(
        system_prompt="Extract all fruits mentioned in the text.",
        user_prompt=request.prompt,
        response_model=LLMTestResponse,
    )


# ── Test Resume Parser ─────────────────────────────────────────────────────────


class ParserTestRequest(BaseModel):
    text: str = Field(..., description="Raw resume or JD text to parse")


@router.post("/parse-resume", response_model=ParsedResume, summary="Test resume parser")
def test_parse_resume(request: ParserTestRequest):
    """Parse raw resume text into structured data. Tests the resume extraction pipeline."""
    from app.core.resume_parser import parse_resume
    from app.models.schemas import ResumeInput
    return parse_resume(ResumeInput(text=request.text))


# ── Test JD Parser ─────────────────────────────────────────────────────────────


@router.post("/parse-jd", response_model=ParsedJobDescription, summary="Test JD parser")
def test_parse_jd(request: ParserTestRequest):
    """Parse raw JD text into structured requirements. Tests the JD extraction pipeline."""
    from app.core.jd_parser import parse_jd
    from app.models.schemas import JDInput
    return parse_jd(JDInput(text=request.text))
