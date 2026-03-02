"""LLM service — structured, constrained interaction with language models.

This is the sole interface between our application and the LLM provider.
All calls enforce: temperature 0, structured JSON output, Pydantic validation,
and a single retry on validation failure.

Compatible with both Ollama (local) and OpenAI (cloud). Uses the simpler
{"type": "json_object"} response format for broad compatibility, with the
JSON schema embedded in the system prompt for guidance.
"""

import json
import logging
from typing import Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# ── Client ──────────────────────────────────────────────────────────────────────


def _get_client() -> OpenAI:
    """Create an OpenAI-compatible client from centralized settings."""
    return OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


def _build_schema_prompt(model_class: Type[T]) -> str:
    """Generate a prompt fragment that instructs the LLM to return JSON
    matching the Pydantic model's schema.

    This is used instead of OpenAI's strict json_schema response_format
    for compatibility with Ollama and other local providers.
    """
    schema = model_class.model_json_schema()
    return (
        "You MUST respond with a valid JSON object that conforms to this schema:\n"
        f"```json\n{json.dumps(schema, indent=2)}\n```\n"
        "Return ONLY the JSON object. No markdown, no explanation, no extra text."
    )


# ── Public API ──────────────────────────────────────────────────────────────────


def call_llm(
    system_prompt: str,
    user_prompt: str,
    response_model: Type[T],
    model: str | None = None,
) -> T:
    """Send a constrained extraction request to the LLM and return a validated
    Pydantic model instance.

    Hard constraints (from design principles):
    - Temperature is 0 for deterministic results
    - All calls use JSON object mode with schema in prompt
    - Responses are validated against the Pydantic model
    - Failed validations retry once, then raise

    Args:
        system_prompt: Instructions for the LLM's role and constraints.
        user_prompt: The actual text to process (resume / JD).
        response_model: Pydantic model class the response must conform to.
        model: Model identifier. Defaults to settings.model.

    Returns:
        A validated instance of response_model.

    Raises:
        ValueError: If the LLM response fails Pydantic validation after retry.
        RuntimeError: If the LLM API call itself fails.
    """
    client = _get_client()
    effective_model = model or settings.model

    # Embed the JSON schema in the system prompt for Ollama compatibility
    schema_instruction = _build_schema_prompt(response_model)
    full_system_prompt = f"{system_prompt}\n\n{schema_instruction}"

    messages = [
        {"role": "system", "content": full_system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    last_error: Exception | None = None

    for attempt in range(1 + settings.max_retries):
        try:
            raw_response = _chat_completion(client, effective_model, messages)
            return _parse_and_validate(raw_response, response_model)

        except (ValidationError, json.JSONDecodeError) as exc:
            last_error = exc
            is_json_error = isinstance(exc, json.JSONDecodeError)
            logger.warning(
                "LLM response failed %s (attempt %d/%d): %s",
                "JSON parsing" if is_json_error else "Pydantic validation",
                attempt + 1,
                1 + settings.max_retries,
                str(exc) if is_json_error else exc.error_count(),
            )
            # On retry, append the error so the LLM can self-correct
            if attempt < settings.max_retries:
                messages.append({"role": "assistant", "content": raw_response})
                if is_json_error:
                    messages.append({
                        "role": "user",
                        "content": (
                            "Your previous response was NOT valid JSON. "
                            f"JSON parse error: {exc}\n\n"
                            "Return ONLY a valid JSON object. No markdown, no "
                            "explanation, no trailing text after the closing brace."
                        ),
                    })
                else:
                    messages.append({
                        "role": "user",
                        "content": (
                            "Your previous response failed schema validation with the "
                            f"following errors:\n{exc}\n\n"
                            "Fix ONLY the fields that failed validation. Use EXACTLY the "
                            "allowed values shown in the error messages above — do not "
                            "use synonyms or paraphrases. Return the full corrected JSON."
                        ),
                    })

    raise ValueError(
        f"LLM response did not conform to {response_model.__name__} after "
        f"{1 + settings.max_retries} attempts. Last validation error: {last_error}"
    )


# ── Internal helpers ────────────────────────────────────────────────────────────


def _chat_completion(
    client: OpenAI,
    model: str,
    messages: list[dict],
) -> str:
    """Make the raw API call. Returns the response content string.

    Uses {"type": "json_object"} format for broad compatibility
    (works with both Ollama and OpenAI).

    Raises RuntimeError on API-level failures.
    """
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=settings.temperature,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        raise RuntimeError(f"LLM API call failed: {exc}") from exc

    content = completion.choices[0].message.content
    if content is None:
        raise RuntimeError("LLM returned an empty response (content is None).")
    return content


def _parse_and_validate(raw_json: str, model_class: Type[T]) -> T:
    """Parse a JSON string and validate it against the Pydantic model.

    Raises ValidationError if the JSON doesn't match the schema.
    """
    data = json.loads(raw_json)
    return model_class.model_validate(data)
