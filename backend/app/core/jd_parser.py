"""Job description parsing — extract structured requirements from JD text via constrained LLM."""

import logging

from app.models.schemas import JDInput, ParsedJobDescription
from app.services.llm import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a job description parser for tech-industry roles. Your job is to extract \
structured requirements from the raw job description text provided by the user.

RULES — follow these exactly:
1. Every requirement in the JD must become one JDRequirement entry.
2. Preserve the JD's original language in the "description" field — do not \
paraphrase or summarize.
3. Classify each requirement:
   - priority: "required" if it is a must-have (e.g. "must have", "required", \
listed under requirements). "preferred" if nice-to-have (e.g. "nice to have", \
"preferred", "bonus", "plus").
   - category: one of "skill", "experience", "education", "certification", \
"responsibility".
4. For "min_years": extract the number only if the JD explicitly states a \
year requirement (e.g. "5+ years of Python" → 5, "3-5 years" → 3). \
If no years are mentioned, leave it as null.
5. Extract "role_title" (e.g. "Senior Software Engineer") and "role_level" \
(e.g. "Senior", "Staff", "Entry-level") if stated. Leave as null if not clear.
6. Do not invent requirements that are not in the text.
7. Do NOT include the raw_text field in your response — it will be added automatically.
"""


def parse_jd(jd: JDInput) -> ParsedJobDescription:
    """Extract structured requirements from raw job description text.

    Args:
        jd: Raw JD input containing plain text.

    Returns:
        ParsedJobDescription with extracted requirements. Preserves
        original JD language for citation in findings.

    Raises:
        ValueError: If LLM output fails validation after retries.
        RuntimeError: If the LLM API call fails.
    """
    text = jd.text.strip()
    if not text:
        logger.info("Empty JD text received, returning empty ParsedJobDescription.")
        return ParsedJobDescription()

    result = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=text,
        response_model=ParsedJobDescription,
    )

    # Attach the original text for downstream citation
    result.raw_text = text
    return result
