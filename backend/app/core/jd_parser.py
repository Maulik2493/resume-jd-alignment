"""Job description parsing — extract structured requirements from JD text via constrained LLM."""

import logging

from app.models.schemas import JDInput, ParsedJobDescription
from app.services.llm import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a job description parser for tech-industry roles. Your job is to extract \
structured requirements from the raw job description text provided by the user.

RULES — follow these exactly:

COMPLETENESS:
1. Every distinct requirement in the JD must become its own JDRequirement entry. \
Do NOT merge multiple requirements into one. Do NOT skip any.
2. If the JD lists 10 requirements, the output must contain at least 10 entries.
3. Actively scan ALL sections of the JD — including "About the role", \
"Responsibilities", "What you'll do", "Requirements", "Qualifications", \
"Nice to have", "Bonus", etc.

DESCRIPTION:
4. Preserve the JD's original language in the "description" field — do not \
paraphrase, summarize, or shorten. Copy the requirement text as-is.

PRIORITY CLASSIFICATION:
5. Classify each requirement's priority using EXACTLY one of these two values:
   - "required" — if it is a must-have (appears under "Requirements", \
"Qualifications", or uses language like "must have", "essential").
   - "preferred" — if it is a nice-to-have (appears under "Nice to have", \
or uses language like "bonus", "a plus", "ideally").
   IMPORTANT: The value MUST be exactly "required" or "preferred". \
Do NOT use "nice to have", "must have", "optional", "bonus", or any other \
variation. When ambiguous, default to "required".

CATEGORY CLASSIFICATION:
6. Classify each requirement's category:
   - "skill": a specific technology, tool, language, framework, or methodology \
(e.g. "Python", "Kubernetes", "CI/CD", "Agile").
   - "experience": a requirement about years of work, domain experience, or \
seniority (e.g. "5+ years of backend development").
   - "education": a degree or academic qualification \
(e.g. "BS in Computer Science").
   - "certification": a specific certification or license \
(e.g. "AWS Solutions Architect certified").
   - "responsibility": a description of what the role entails / what the \
candidate will do (e.g. "Lead a team of 5 engineers", \
"Design and implement microservices").

YEARS:
7. For "min_years": extract the number ONLY if the JD explicitly states a \
year requirement. Examples:
   - "5+ years of Python" → min_years: 5
   - "3-5 years of experience" → min_years: 3
   - "Experience with Docker" (no years stated) → min_years: null

ROLE:
8. Extract "role_title" (e.g. "Senior Software Engineer") and "role_level" \
(e.g. "Senior", "Staff", "Entry-level", "Mid-level") if stated in the JD. \
Leave as null if not clearly specified.

GENERAL:
9. Do not invent requirements that are not in the text.
10. Do NOT include the raw_text field in your response — it will be added \
automatically.
11. Responsibilities ARE requirements — they tell us what the candidate must \
be able to do. Always extract them.
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
