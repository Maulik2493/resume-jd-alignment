"""Job description parsing — extract structured requirements from JD text."""

from app.models.schemas import JDInput


def parse_jd(jd: JDInput) -> dict:
    """Extract structured requirements from raw job description text.

    Args:
        jd: Raw JD input containing plain text.

    Returns:
        Dict with extracted requirements: required_skills, preferred_skills,
        experience_requirements, education_requirements, certifications.
        Preserves original JD language for citation in findings.
    """
    # TODO: Implement structured extraction via constrained LLM call
    return {
        "required_skills": [],
        "preferred_skills": [],
        "experience_requirements": [],
        "education_requirements": [],
        "certifications": [],
    }
