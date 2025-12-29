"""Watermark system for Hypertext cards."""

from hypertext.watermark.crypto import (
    load_card_identity,
    canonical_payload,
    compute_signature_hex,
    signature_bits,
    build_svg,
)
from hypertext.watermark.apply import apply_watermark
from hypertext.watermark.verify import verify_watermark

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
