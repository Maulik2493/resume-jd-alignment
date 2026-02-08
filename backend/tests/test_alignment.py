"""Tests for the core alignment engine."""

from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ResumeInput,
    JDInput,
)
from app.core.alignment import run_alignment


def test_empty_inputs_return_empty_findings():
    """Given empty resume and JD text, the engine should return no findings."""
    request = AnalyzeRequest(
        resume=ResumeInput(text=""),
        jd=JDInput(text=""),
    )
    response = run_alignment(request)
    assert isinstance(response, AnalyzeResponse)
    assert response.category_a == []
    assert response.category_b == []
