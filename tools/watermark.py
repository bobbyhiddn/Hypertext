#!/usr/bin/env python3
import argparse
import hmac
import hashlib
import json
import os
import sys
from pathlib import Path


def _load_card_identity(card_dir: Path) -> dict:
    card_path = card_dir / "card.json"
    if not card_path.exists():
        raise FileNotFoundError(f"Missing {card_path}")

    with open(card_path, "r", encoding="utf-8") as f:
        card = json.load(f)

    content = card.get("content", {}) if isinstance(card.get("content"), dict) else {}

    return {
        "series": str(content.get("SERIES", "")).strip(),
        "number": str(content.get("NUMBER", "")).strip(),
        "word": str(content.get("WORD", "")).strip(),
        "rarity": str(content.get("RARITY_TEXT", "")).strip(),
        "card_type": str(content.get("CARD_TYPE", "")).strip(),
    }


def _canonical_payload(identity: dict) -> str:
    # Intentionally strict ordering and separators.
    return (
        f"series={identity.get('series','')}|"
        f"number={identity.get('number','')}|"
        f"word={identity.get('word','')}|"
        f"rarity={identity.get('rarity','')}|"
        f"card_type={identity.get('card_type','')}"
    )


def _get_key() -> bytes:
    key = os.environ.get("HYPERTEXT_SIGNING_KEY")
    if not key:
        raise RuntimeError("Missing env var HYPERTEXT_SIGNING_KEY")
    return key.encode("utf-8")


def compute_signature_hex(payload: str) -> str:
    key = _get_key()
    sig = hmac.new(key, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return sig


def signature_bits(sig_hex: str, bit_count: int) -> list[int]:
    # Convert hex -> bits MSB first
    raw = bytes.fromhex(sig_hex)
    bits: list[int] = []
    for b in raw:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
            if len(bits) >= bit_count:
                return bits
    return bits[:bit_count]


def build_svg(*, sig_hex: str, payload: str, size_px: int = 72) -> str:
    # 5x5 grid = 25 bits
    bits = signature_bits(sig_hex, 25)

    # Viewbox units
    vb = 100
    pad = 6
    center = vb / 2

    # Diamond border polygon
    diamond = f"{center},{pad} {vb - pad},{center} {center},{vb - pad} {pad},{center}"

    # Grid area inside diamond
    grid_n = 5
    grid_size = 58
    grid_x0 = (vb - grid_size) / 2
    grid_y0 = (vb - grid_size) / 2
    cell = grid_size / grid_n
    dot = cell * 0.62
    dot_pad = (cell - dot) / 2

    # Color tuned for subtle bottom-right watermark
    stroke = "#0a192f"
    fill = "#c5a059"

    rects = []
    idx = 0
    for r in range(grid_n):
        for c in range(grid_n):
            if bits[idx] == 1:
                x = grid_x0 + c * cell + dot_pad
                y = grid_y0 + r * cell + dot_pad
                rects.append(
                    f"<rect x=\"{x:.2f}\" y=\"{y:.2f}\" width=\"{dot:.2f}\" height=\"{dot:.2f}\" rx=\"1.4\" fill=\"{fill}\" opacity=\"0.62\" />"
                )
            idx += 1

    # Embed signature for verifier (requires secret); no secret is stored.
    sig_short = sig_hex[:16]

    return "\n".join(
        [
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            f"<!-- hypertext_sig:{sig_hex} -->",
            f"<!-- hypertext_payload:{payload} -->",
            f"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{size_px}\" height=\"{size_px}\" viewBox=\"0 0 {vb} {vb}\">",
            f"  <g>",
            f"    <polygon points=\"{diamond}\" fill=\"none\" stroke=\"{stroke}\" stroke-width=\"2.2\" opacity=\"0.55\" />",
            f"    <polygon points=\"{diamond}\" fill=\"none\" stroke=\"{fill}\" stroke-width=\"1.2\" opacity=\"0.38\" />",
            "    " + "\n    ".join(rects) if rects else "",
            f"    <circle cx=\"{center}\" cy=\"{center}\" r=\"2.2\" fill=\"{fill}\" opacity=\"0.35\" />",
            f"  </g>",
            f"</svg>",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate cryptographic watermark SVG")
    parser.add_argument("--card-dir", required=True, help="Card directory (contains card.json)")
    parser.add_argument("--out", help="Output SVG path (default: <card-dir>/watermark.svg)")
    parser.add_argument("--size", type=int, default=72, help="SVG pixel size")
    args = parser.parse_args()

    card_dir = Path(args.card_dir)
    out_path = Path(args.out) if args.out else (card_dir / "watermark.svg")

    identity = _load_card_identity(card_dir)
    payload = _canonical_payload(identity)
    sig_hex = compute_signature_hex(payload)
    svg = build_svg(sig_hex=sig_hex, payload=payload, size_px=int(args.size))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)

    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
