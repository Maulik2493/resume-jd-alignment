"""Text utilities — cleaning, normalization, and helper functions."""

import re


def clean_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters into single spaces and strip."""
    return re.sub(r"\s+", " ", text).strip()


def is_empty(text: str) -> bool:
    """Check if text is empty or contains only whitespace."""
    return not text or not text.strip()
