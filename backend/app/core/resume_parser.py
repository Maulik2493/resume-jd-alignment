"""Resume parsing — extract structured data from resume text."""

from app.models.schemas import ResumeInput


def parse_resume(resume: ResumeInput) -> dict:
    """Extract structured data from raw resume text.

    Args:
        resume: Raw resume input containing plain text.

    Returns:
        Dict with extracted sections: skills, experience, education, certifications.
        Only includes what is explicitly stated in the text.
    """
    # TODO: Implement structured extraction via constrained LLM call
    return {
        "skills": [],
        "experience": [],
        "education": [],
        "certifications": [],
    }
