"""Shared configuration for Gemini image generation."""

import os

DEFAULT_IMAGE_MODEL = "gemini-3.1-flash-image"
DEFAULT_TEXT_MODEL = "gemini-3.7-flash"
DEFAULT_REVIEW_MODEL = "gemini-3.7-flash"
IMAGE_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def image_model() -> str:
    """Return the configured image model, preserving an operator override."""
    return os.environ.get("GEMINI_IMAGE_MODEL", DEFAULT_IMAGE_MODEL)


def text_model() -> str:
    """Return the stable text model used by random-card planning."""
    return os.environ.get("GEMINI_TEXT_MODEL", DEFAULT_TEXT_MODEL)


def review_model() -> str:
    """Return the stable review model used for automated card checks."""
    return os.environ.get("GEMINI_REVIEW_MODEL", DEFAULT_REVIEW_MODEL)


def image_endpoint(model: str | None = None) -> str:
    return f"{IMAGE_API_BASE}/{model or image_model()}:generateContent"
