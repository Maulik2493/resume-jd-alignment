"""Core alignment engine — compare resume against JD and produce Category A/B findings."""

from typing import List

from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    CategoryASuggestion,
    CategoryBFeedback,
)


def run_alignment(request: AnalyzeRequest) -> AnalyzeResponse:
    """Compare a resume against a JD and produce categorized findings.

    Category A — improvements that can be made without changing the truth.
    Category B — real gaps that require actual experience.

    Every finding must include a justification citing specific JD requirements
    and resume content (or absence thereof).

    Args:
        request: Contains resume and JD text inputs.

    Returns:
        AnalyzeResponse with category_a and category_b findings.
    """
    # TODO: Wire up resume_parser, jd_parser, and comparison logic
    category_a: List[CategoryASuggestion] = []
    category_b: List[CategoryBFeedback] = []

    return AnalyzeResponse(category_a=category_a, category_b=category_b)
