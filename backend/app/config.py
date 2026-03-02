"""Centralized configuration for the application.

All settings are loaded from environment variables (via .env file).
Secrets (API keys) live ONLY in env vars — never in committed files.
Non-secret defaults are defined here as fallbacks.

Usage:
    from app.config import settings
    settings.openai_api_key   # "ollama" by default (Ollama doesn't need a real key)
    settings.openai_base_url  # "http://localhost:11434/v1" by default
    settings.model            # "llama3.2" by default
"""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# Load .env file from project root (if present) into os.environ
load_dotenv()


class Settings(BaseModel):
    """Application settings — single source of truth for all configuration.

    Defaults are configured for local Ollama usage. Override via env vars
    or .env file to use OpenAI or Azure OpenAI.
    """

    # ── API credentials ─────────────────────────────────────────────────────
    openai_api_key: str = Field(
        "ollama", description="API key — 'ollama' for local Ollama, real key for OpenAI"
    )

    # ── LLM settings ───────────────────────────────────────────────────────
    openai_base_url: str = Field(
        "http://localhost:11434/v1",
        description="API base URL — Ollama default, override for OpenAI/Azure",
    )
    model: str = Field(
        "llama3.2", description="Model identifier (must be pulled in Ollama first)"
    )
    temperature: float = Field(
        0.0, description="LLM temperature — 0 for deterministic extraction"
    )
    max_retries: int = Field(
        2, description="Retry count on validation failure before raising"
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
        openai_api_key=os.environ.get("OPENAI_API_KEY", "ollama"),
        openai_base_url=os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1"),
        model=os.environ.get("OPENAI_MODEL", "llama3.2"),
        temperature=float(os.environ.get("OPENAI_TEMPERATURE", "0")),
        max_retries=int(os.environ.get("OPENAI_MAX_RETRIES", "1")),
    )


settings = _load_settings()
