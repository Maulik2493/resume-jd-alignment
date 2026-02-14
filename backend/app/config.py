"""Centralized configuration for the application.

All settings are loaded from environment variables (via .env file).
Secrets (API keys) live ONLY in env vars — never in committed files.
Non-secret defaults are defined here as fallbacks.

Usage:
    from app.config import settings
    settings.openai_api_key  # raises at startup if missing
    settings.model           # "gpt-4o-mini" unless overridden
"""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# Load .env file from project root (if present) into os.environ
load_dotenv()


class Settings(BaseModel):
    """Application settings — single source of truth for all configuration.

    Secrets are required (no defaults). Non-secrets have sensible defaults
    that can be overridden via env vars.
    """

    # ── Secrets (no defaults — must be set in env) ──────────────────────────
    openai_api_key: str = Field(
        ..., description="OpenAI API key — required"
    )

    # ── LLM settings ───────────────────────────────────────────────────────
    openai_base_url: str | None = Field(
        None, description="Custom base URL for Azure OpenAI or proxies"
    )
    model: str = Field(
        "gpt-4o-mini", description="OpenAI model identifier"
    )
    temperature: float = Field(
        0.0, description="LLM temperature — 0 for deterministic extraction"
    )
    max_retries: int = Field(
        1, description="Retry count on validation failure before raising"
    )

    @field_validator("temperature")
    @classmethod
    def temperature_must_be_near_zero(cls, v: float) -> float:
        if v > 0.2:
            raise ValueError(
                f"Temperature {v} is too high. Design principles require 0 or near-0 "
                "for deterministic extraction."
            )
        return v


def _load_settings() -> Settings:
    """Build Settings from environment variables.

    Raises a clear error at startup if required vars are missing,
    rather than failing at first LLM call.
    """
    return Settings(
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        openai_base_url=os.environ.get("OPENAI_BASE_URL"),
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=float(os.environ.get("OPENAI_TEMPERATURE", "0")),
        max_retries=int(os.environ.get("OPENAI_MAX_RETRIES", "1")),
    )


settings = _load_settings()
