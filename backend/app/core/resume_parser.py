"""Resume parsing — extract structured data from resume text via constrained LLM."""

import logging
import re
from datetime import datetime

from app.models.schemas import ParsedResume, ResumeInput
from app.services.llm import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a resume parser for tech-industry resumes. Your job is to extract \
structured data from the raw resume text provided by the user.

RULES — follow these exactly:

CONTACT INFO:
1. Copy the name, email, phone, and location EXACTLY as they appear in the \
resume text — character for character. Do NOT retype or paraphrase them.

SKILLS:
2. Extract skills from TWO sources:
   a) EXPLICIT — skills listed in a dedicated "Skills", "Technical Skills", \
or "Technologies" section. Mark these as source: "explicit".
   b) INFERRED — skills, tools, frameworks, or methodologies mentioned ONLY \
within work-experience bullets, project descriptions, or internship sections \
(e.g. "JWT", "JDBC", "Agile", "CI/CD"). Mark these as source: \
"inferred_from_experience". You MUST actively scan all experience and project \
text for these.
3. Do NOT put certifications or course names in the skills list. \
A certification (e.g. "AWS Solutions Architect – Amazon") belongs in \
certifications, not skills.
4. Concepts like "Data Structures", "OOP", "DBMS" from a skills section are \
valid explicit skills. But "Data Structures and Algorithms – Udemy" is a \
certification, not a skill.

EXPERIENCE:
5. Preserve the original phrasing of bullet points — do not rewrite or summarize.
6. For "technologies" on each experience entry: read every bullet in that \
entry and list every technology, tool, framework, language, or platform \
explicitly named. This list is PER ENTRY, not global. Example: if a bullet \
says "Built REST APIs using Node.js and Express", technologies should include \
["Node.js", "Express", "REST APIs"].
7. Do NOT compute "duration_months" — leave it as null. It will be calculated \
automatically.
8. For "start_date" and "end_date": ALWAYS normalize dates to YYYY-MM format. \
Examples:
   - "Jan 2020" → "2020-01"
   - "January 2020" → "2020-01"
   - "05/2024" → "2024-05"
   - "2020" (year only, no month) → "2020-01"
   - If the end date is "Present", "Current", or similar → use "Present".

PROJECTS:
8. Extract ALL projects listed in the resume. Do not skip or truncate any. \
If the resume lists 5 projects, the output must contain exactly 5.
9. For "technologies" on each project: read the project description and list \
every technology, tool, framework, language, or platform explicitly named. \
Example: "Used MongoDB for storing user and job data" → include "MongoDB".
10. Preserve the project description in original phrasing.

CERTIFICATIONS:
11. Items under a "Certifications" or "Licenses" section are certifications, \
NOT skills. Each certification entry should have:
    - name: the certification title (e.g. "Data Structures and Algorithms")
    - issuer: the issuing organization or platform (e.g. "Udemy", "Coursera", \
"AWS") if mentioned
    - year: year of completion if mentioned

EDUCATION:
12. Extract all education entries. Preserve institution name, degree, field, \
and year as written.

GENERAL:
13. If a section does not exist in the resume, return an empty list — do not \
fabricate content.
14. Do NOT include the raw_text field in your response — it will be added \
automatically.
15. When in doubt whether something is a skill vs. certification: if it has \
a provider/platform name (Udemy, Coursera, AWS, Google, etc.), it is a \
certification.
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

    # ── Deterministic post-processing ───────────────────────────────────────
    # These corrections fix known LLM weaknesses with rule-based logic.

    _fix_contact_email(result, text)
    _compute_durations(result)

    # Attach the original text for downstream citation
    result.raw_text = text
    return result


# ── Post-processing helpers ─────────────────────────────────────────────────


def _find_emails_in_text(text: str) -> list[str]:
    """Extract all email addresses from raw text using regex."""
    return re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)


def _fix_contact_email(result: ParsedResume, raw_text: str) -> None:
    """Verify extracted email against raw text.

    LLMs regenerate text token-by-token and can introduce typos in emails.
    If the extracted email doesn't appear in the raw text, replace it with
    the closest match found in the source.
    """
    if not result.contact_info.email:
        return

    extracted = result.contact_info.email
    if extracted in raw_text:
        return  # Exact match — no correction needed

    # Find all emails in source text and pick the closest match
    source_emails = _find_emails_in_text(raw_text)
    if not source_emails:
        logger.warning(
            "Extracted email '%s' not found in raw text and no emails found in source.",
            extracted,
        )
        return

    # Simple heuristic: pick the email that shares the most characters
    best_match = max(source_emails, key=lambda e: _char_overlap(e, extracted))
    if best_match != extracted:
        logger.info(
            "Corrected email from LLM output: '%s' → '%s' (matched from raw text)",
            extracted,
            best_match,
        )
        result.contact_info.email = best_match


def _char_overlap(a: str, b: str) -> int:
    """Count the number of positional character matches between two strings."""
    return sum(ca == cb for ca, cb in zip(a, b))


# ── Duration calculation ─────────────────────────────────────────────────────


def _parse_yyyy_mm(date_str: str | None) -> datetime | None:
    """Parse a YYYY-MM date string or 'Present' into a datetime.

    The LLM is instructed to normalize all dates to YYYY-MM format,
    so this parser only needs to handle that single format.
    """
    if not date_str:
        return None

    cleaned = date_str.strip().lower()

    if cleaned in ("present", "current", "now", "ongoing"):
        return datetime.now()

    match = re.match(r"^(\d{4})-(\d{2})$", cleaned)
    if match:
        return datetime(int(match.group(1)), int(match.group(2)), 1)

    logger.warning("Unexpected date format from LLM: '%s' (expected YYYY-MM)", date_str)
    return None


def _compute_durations(result: ParsedResume) -> None:
    """Compute duration_months deterministically from start_date and end_date.

    Dates are expected in YYYY-MM format (enforced by the prompt).
    LLMs are unreliable at date arithmetic, so we always compute this
    in Python rather than trusting the LLM's calculation.
    """
    for entry in result.experience:
        start = _parse_yyyy_mm(entry.start_date)
        end = _parse_yyyy_mm(entry.end_date)
        if start and end and end >= start:
            months = (end.year - start.year) * 12 + (end.month - start.month)
            entry.duration_months = max(months, 1)  # At least 1 month
        else:
            entry.duration_months = None
