"""LLM service — structured, constrained interaction with language models."""

import os
from typing import Any, Dict


def call_llm(prompt: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Send a constrained request to the LLM and return structured output.

    Hard constraints (from design principles):
    - Temperature is set to 0 for deterministic results
    - All calls use structured output (JSON mode)
    - Responses are validated against the provided schema
    - Failed validations raise an error — never silently patched

    Args:
        prompt: The fully constructed prompt with explicit constraints.
        response_schema: Expected JSON schema the response must conform to.

    Returns:
        Parsed and validated dict matching the response_schema.

    Raises:
        ValueError: If the LLM response does not conform to the schema.
        RuntimeError: If the LLM API call fails.
    """
    # TODO: Implement actual LLM API call (OpenAI / Azure OpenAI)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in environment variables.")

    raise NotImplementedError("LLM integration not yet implemented.")
