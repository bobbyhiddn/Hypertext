"""Card generation and processing for Hypertext.

Exports are lazily loaded to avoid import conflicts when running
submodules directly with `python -m hypertext.cards.<module>`.
"""

__all__ = [
    # render.py
    "render_post",
    "POST_TEMPLATE",
    # composite.py
    "composite_card",
    "CARD_WIDTH",
    "CARD_HEIGHT",
    "COLORS",
    "REGIONS",
    # clean.py
    "clean_template",
    # validate.py
    "validate_card_file",
    "lint_card",
    "load_card",
    "load_schema",
]


def __getattr__(name: str):
    """Lazy import for module exports."""
    if name in ("render_post", "POST_TEMPLATE"):
        from hypertext.cards import render
        return getattr(render, name)
    elif name in ("composite_card", "CARD_WIDTH", "CARD_HEIGHT", "COLORS", "REGIONS"):
        from hypertext.cards import composite
        return getattr(composite, name)
    elif name == "clean_template":
        from hypertext.cards import clean
        return getattr(clean, name)
    elif name in ("validate_card_file", "lint_card", "load_card", "load_schema"):
        from hypertext.cards import validate
        return getattr(validate, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
