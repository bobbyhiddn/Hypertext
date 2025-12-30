"""Gemini API wrappers for Hypertext."""

from hypertext.gemini.text import generate_text, generate_text_with_grounding
from hypertext.gemini.image import generate_image
from hypertext.gemini.style import generate_with_styles, generate_with_style
from hypertext.gemini.review import (
    CardDescription,
    ReviewResult,
    describe_card,
    describe_card_style_references,
    score_against_rubric,
    review_card,
    format_description_report,
    format_review_report,
)

__all__ = [
    # text.py
    "generate_text",
    "generate_text_with_grounding",
    # image.py
    "generate_image",
    # style.py
    "generate_with_styles",
    "generate_with_style",
    # review.py
    "CardDescription",
    "ReviewResult",
    "describe_card",
    "describe_card_style_references",
    "score_against_rubric",
    "review_card",
    "format_description_report",
    "format_review_report",
]
