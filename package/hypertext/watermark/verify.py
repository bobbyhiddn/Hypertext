#!/usr/bin/env python3
"""Verify watermark authenticity against card.json and signing key."""

import argparse
import re
from pathlib import Path

from hypertext.watermark.crypto import (
    load_card_identity,
    canonical_payload,
    compute_signature_hex,
)


def _read_file(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _extract_sig(svg_text: str) -> str | None:
    m = re.search(r"hypertext_sig:([0-9a-f]{64})", svg_text)
    if not m:
        return None
    return m.group(1)


def verify_watermark(card_dir: Path, svg_path: Path | None = None) -> tuple[bool, str]:
    """Verify watermark matches card identity.

    Returns:
        Tuple of (is_valid, message)
    """
    svg_path = svg_path or (card_dir / "watermark.svg")
    if not svg_path.exists():
        return False, f"Missing {svg_path}"

    identity = load_card_identity(card_dir)
    payload = canonical_payload(identity)
    expected = compute_signature_hex(payload)

    svg_text = _read_file(svg_path)
    actual = _extract_sig(svg_text)
    if not actual:
        return False, "Could not find embedded hypertext_sig in watermark.svg"

    if actual != expected:
        return False, f"Signature mismatch: expected={expected}, actual={actual}"

    return True, "OK"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify watermark.svg against card.json + signing key")
    parser.add_argument("--card-dir", required=True)
    parser.add_argument("--svg", help="Path to watermark.svg (default: <card-dir>/watermark.svg)")
    args = parser.parse_args()

    card_dir = Path(args.card_dir)
    svg_path = Path(args.svg) if args.svg else None

    is_valid, message = verify_watermark(card_dir, svg_path)
    print(message)

    if not is_valid:
        return 1 if "mismatch" in message.lower() else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
