"""LLM service — structured, constrained interaction with language models.

This is the sole interface between our application and the LLM provider.
All calls enforce: temperature 0, structured JSON output, Pydantic validation,
and a single retry on validation failure.
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
    """Create an OpenAI client from centralized settings."""
    return OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


def _build_json_schema(model_class: Type[T]) -> dict:
    """Generate OpenAI-compatible JSON schema from a Pydantic model.

    Wraps the model's JSON schema in the envelope format required by
    OpenAI's `response_format` parameter.
    """
    return {
        "type": "json_schema",
        "json_schema": {
            "name": model_class.__name__,
            "strict": True,
            "schema": model_class.model_json_schema(),
        },
    }


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
    - All calls use structured output (JSON mode with schema)
    - Responses are validated against the Pydantic model
    - Failed validations retry once, then raise

    Args:
        system_prompt: Instructions for the LLM's role and constraints.
        user_prompt: The actual text to process (resume / JD).
        response_model: Pydantic model class the response must conform to.
        model: OpenAI model identifier. Defaults to settings.model.

    Returns:
        A validated instance of response_model.

    Raises:
        ValueError: If the LLM response fails Pydantic validation after retry.
        RuntimeError: If the LLM API call itself fails.
    """
    client = _get_client()
    effective_model = model or settings.model
    response_format = _build_json_schema(response_model)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    last_error: Exception | None = None

    for attempt in range(1 + settings.max_retries):
        try:
            raw_response = _chat_completion(client, effective_model, messages, response_format)
            return _parse_and_validate(raw_response, response_model)

        except ValidationError as exc:
            last_error = exc
            logger.warning(
                "LLM response failed Pydantic validation (attempt %d/%d): %s",
                attempt + 1,
                1 + settings.max_retries,
                exc.error_count(),
            )
            # On retry, append the validation error so the LLM can self-correct
            if attempt < settings.max_retries:
                messages.append({"role": "assistant", "content": raw_response})
                messages.append({
                    "role": "user",
                    "content": (
                        "Your previous response failed schema validation with the "
                        f"following errors:\n{exc}\n\n"
                        "Please return a corrected JSON object."
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
    response_format: dict,
) -> str:
    """Make the raw API call. Returns the response content string.

    Raises RuntimeError on API-level failures.
    """
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=settings.temperature,
            response_format=response_format,
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI API call failed: {exc}") from exc

    content = completion.choices[0].message.content
    if content is None:
        raise RuntimeError("OpenAI returned an empty response (content is None).")
    return content


def _parse_and_validate(raw_json: str, model_class: Type[T]) -> T:
    """Parse a JSON string and validate it against the Pydantic model.

    Raises ValidationError if the JSON doesn't match the schema.
    """
    data = json.loads(raw_json)
    return model_class.model_validate(data)
