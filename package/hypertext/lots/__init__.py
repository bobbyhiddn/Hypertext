"""Lot (Phase Card) generation system for Hypertext."""


def __getattr__(name: str):
    """Lazy imports to avoid circular import warnings when running as script."""
    if name in (
        "load_universal_phases",
        "load_series_content",
        "get_series_theme",
        "phase_init",
        "phase_generate",
        "phase_render",
        "phase_batch",
        "phase_export",
        "phase_grade",
        "describe_lot_card",
        "describe_style_references",
        "score_lot_card",
        "LotDescription",
        "LotGradeResult",
        "GRADING_MODEL",
    ):
        from hypertext.lots import generation
        return getattr(generation, name)

    if name in ("render_lot_card", "render_lot_card_with_series", "TYPE_ICONS"):
        from hypertext.lots import renderer
        return getattr(renderer, name)

    if name in ("export_for_platform", "list_platforms", "PLATFORMS"):
        from hypertext.lots import exporter
        return getattr(exporter, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # generation.py
    "load_universal_phases",
    "load_series_content",
    "get_series_theme",
    "phase_init",
    "phase_generate",
    "phase_render",
    "phase_batch",
    "phase_export",
    "phase_grade",
    "describe_lot_card",
    "describe_style_references",
    "score_lot_card",
    "LotDescription",
    "LotGradeResult",
    "GRADING_MODEL",
    # renderer.py
    "render_lot_card",
    "render_lot_card_with_series",
    "TYPE_ICONS",
    # exporter.py
    "export_for_platform",
    "list_platforms",
    "PLATFORMS",
]
