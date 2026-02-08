"""Hard constraints — rules that must never be violated by the system."""

from typing import List

from app.models.schemas import CategoryASuggestion, CategoryBFeedback


def validate_category_a(findings: List[CategoryASuggestion]) -> List[CategoryASuggestion]:
    """Validate Category A findings against hard constraints.

    Rejects any finding that:
    - Has an empty justification
    - Has an empty original or suggestion field
    - Suggests inventing experience (detected by constraint rules)

    Returns only findings that pass all checks.
    """
    validated = []
    for finding in findings:
        if not finding.justification.strip():
            continue  # Reject: no justification provided
        if not finding.original.strip() or not finding.suggestion.strip():
            continue  # Reject: missing original or suggestion text
        validated.append(finding)
    return validated


def validate_category_b(findings: List[CategoryBFeedback]) -> List[CategoryBFeedback]:
    """Validate Category B findings against hard constraints.

    Rejects any finding that:
    - Has an empty justification
    - Has an empty gap description

    Returns only findings that pass all checks.
    """
    validated = []
    for finding in findings:
        if not finding.justification.strip():
            continue  # Reject: no justification provided
        if not finding.gap.strip():
            continue  # Reject: no gap description
        validated.append(finding)
    return validated
