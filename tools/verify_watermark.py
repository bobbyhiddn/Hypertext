#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

from watermark import _load_card_identity, _canonical_payload, compute_signature_hex


def _read_file(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _extract_sig(svg_text: str) -> str | None:
    m = re.search(r"hypertext_sig:([0-9a-f]{64})", svg_text)
    if not m:
        return None
    return m.group(1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify watermark.svg against card.json + signing key")
    parser.add_argument("--card-dir", required=True)
    parser.add_argument("--svg", help="Path to watermark.svg (default: <card-dir>/watermark.svg)")
    args = parser.parse_args()

    card_dir = Path(args.card_dir)
    svg_path = Path(args.svg) if args.svg else (card_dir / "watermark.svg")
    if not svg_path.exists():
        print(f"Missing {svg_path}")
        return 2

    identity = _load_card_identity(card_dir)
    payload = _canonical_payload(identity)
    expected = compute_signature_hex(payload)

    svg_text = _read_file(svg_path)
    actual = _extract_sig(svg_text)
    if not actual:
        print("Could not find embedded hypertext_sig in watermark.svg")
        return 2

    if actual != expected:
        print("FAIL: watermark signature does not match card payload + signing key")
        print(f"expected={expected}")
        print(f"actual  ={actual}")
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
