"""Gemini API wrappers for Hypertext.

Exports are lazily loaded to avoid import conflicts when running
submodules directly with `python -m hypertext.gemini.<module>`.
"""

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


def __getattr__(name: str):
    """Lazy import for module exports."""
    if name in ("generate_text", "generate_text_with_grounding"):
        from hypertext.gemini import text
        return getattr(text, name)
    elif name == "generate_image":
        from hypertext.gemini import image
        return getattr(image, name)
    elif name in ("generate_with_styles", "generate_with_style"):
        from hypertext.gemini import style
        return getattr(style, name)
    elif name in (
        "CardDescription",
        "ReviewResult",
        "describe_card",
        "score_against_rubric",
        "review_card",
        "format_description_report",
        "format_review_report",
    ):
        from hypertext.gemini import review
        return getattr(review, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
