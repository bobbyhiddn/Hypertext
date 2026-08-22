"""Shared configuration for Gemini image generation."""

import os

DEFAULT_IMAGE_MODEL = "gemini-3.1-flash-image"
IMAGE_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def image_model() -> str:
    """Return the configured image model, preserving an operator override."""
    return os.environ.get("GEMINI_IMAGE_MODEL", DEFAULT_IMAGE_MODEL)


def image_endpoint(model: str | None = None) -> str:
    return f"{IMAGE_API_BASE}/{model or image_model()}:generateContent"
