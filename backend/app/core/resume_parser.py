"""Resume parsing — extract structured data from resume text via constrained LLM."""

import logging

from app.models.schemas import ParsedResume, ResumeInput
from app.services.llm import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a resume parser for tech-industry resumes. Your job is to extract \
structured data from the raw resume text provided by the user.

RULES — follow these exactly:
1. Only extract what is explicitly stated or directly implied by the text.
2. Never infer skills that are not supported by the resume content.
3. Preserve the original phrasing of bullet points — do not rewrite or summarize.
4. For the "source" field on skills:
   - Use "explicit" if the skill appears in a dedicated skills/technologies section.
   - Use "inferred_from_experience" if the skill is mentioned only within a \
work-experience bullet or project description.
5. For "technologies" on experience entries and projects, list only technologies \
explicitly named in that section's bullets or description.
6. If a section (e.g. certifications, projects) does not exist in the resume, \
return an empty list for it — do not fabricate content.
7. Calculate "duration_months" only if both start and end dates are clearly stated.
8. Do NOT include the raw_text field in your response — it will be added automatically.
"""


def parse_resume(resume: ResumeInput) -> ParsedResume:
    """Extract structured data from raw resume text.

    Args:
        resume: Raw resume input containing plain text.

    Returns:
        ParsedResume with extracted sections. Only includes what is
        explicitly stated or directly implied by the text.

    Raises:
        ValueError: If LLM output fails validation after retries.
        RuntimeError: If the LLM API call fails.
    """
    text = resume.text.strip()
    if not text:
        logger.info("Empty resume text received, returning empty ParsedResume.")
        return ParsedResume()

    result = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=text,
        response_model=ParsedResume,
    )

    # Attach the original text for downstream citation
    result.raw_text = text
    return result
