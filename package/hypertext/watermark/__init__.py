"""Watermark system for Hypertext cards.

Exports are lazily loaded to avoid import conflicts when running
submodules directly with `python -m hypertext.watermark.<module>`.
"""

__all__ = [
    # crypto.py
    "load_card_identity",
    "canonical_payload",
    "compute_signature_hex",
    "signature_bits",
    "build_svg",
    # apply.py
    "apply_watermark",
    # verify.py
    "verify_watermark",
]


def __getattr__(name: str):
    """Lazy import for module exports."""
    if name in (
        "load_card_identity",
        "canonical_payload",
        "compute_signature_hex",
        "signature_bits",
        "build_svg",
    ):
        from hypertext.watermark import crypto
        return getattr(crypto, name)
    elif name == "apply_watermark":
        from hypertext.watermark import apply
        return getattr(apply, name)
    elif name == "verify_watermark":
        from hypertext.watermark import verify
        return getattr(verify, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
