#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except Exception:
    Image = None
    ImageDraw = None

# Reuse watermark logic
from watermark import _load_card_identity, _canonical_payload, compute_signature_hex, signature_bits


def _require_pillow():
    if Image is None or ImageDraw is None:
        raise RuntimeError("Missing dependency: Pillow. Install with: pip install pillow")


def _draw_diamond_sigil(*, overlay: Image.Image, sig_hex: str, size_px: int) -> None:
    # 5x5 bits
    bits = signature_bits(sig_hex, 25)

    draw = ImageDraw.Draw(overlay)

    # Colors (RGBA)
    navy = (10, 25, 47, 175)
    gold = (197, 160, 89, 185)

    w = h = size_px
    cx = w / 2
    cy = h / 2
    pad = 3

    diamond = [(cx, pad), (w - pad, cy), (cx, h - pad), (pad, cy)]
    draw.polygon(diamond, outline=navy, width=2)
    draw.polygon(diamond, outline=gold, width=1)

    # Grid inside
    grid_n = 5
    grid_size = int(size_px * 0.62)
    x0 = int((w - grid_size) / 2)
    y0 = int((h - grid_size) / 2)
    cell = grid_size / grid_n
    dot = cell * 0.62

    idx = 0
    for r in range(grid_n):
        for c in range(grid_n):
            if bits[idx] == 1:
                x = x0 + c * cell + (cell - dot) / 2
                y = y0 + r * cell + (cell - dot) / 2
                rect = [x, y, x + dot, y + dot]
                draw.rounded_rectangle(rect, radius=2, fill=gold)
            idx += 1

    # Center dot
    r = max(1, int(size_px * 0.03))
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=gold)


def apply_watermark(*, card_dir: Path, in_png: Path, out_png: Path | None, size_px: int, inset_px: int) -> Path:
    _require_pillow()

    if not in_png.exists():
        raise FileNotFoundError(f"Missing {in_png}")

    out_png = out_png or in_png

    identity = _load_card_identity(card_dir)
    payload = _canonical_payload(identity)
    sig_hex = compute_signature_hex(payload)

    img = Image.open(in_png).convert("RGBA")

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sigil = Image.new("RGBA", (size_px, size_px), (0, 0, 0, 0))
    _draw_diamond_sigil(overlay=sigil, sig_hex=sig_hex, size_px=size_px)

    x = img.size[0] - inset_px - size_px - 16
    y = img.size[1] - inset_px - size_px - 8
    overlay.paste(sigil, (x, y), sigil)

    out = Image.alpha_composite(img, overlay).convert("RGB")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_png)

    return out_png


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply watermark to card PNG")
    parser.add_argument("--card-dir", required=True)
    parser.add_argument("--in", dest="in_png", help="Input PNG path (default: <card-dir>/outputs/card_1024x1536.png)")
    parser.add_argument("--out", dest="out_png", help="Output PNG path (default: overwrite input)")
    parser.add_argument("--size", type=int, default=36)
    parser.add_argument("--inset", type=int, default=12)
    args = parser.parse_args()

    card_dir = Path(args.card_dir)
    in_png = Path(args.in_png) if args.in_png else (card_dir / "outputs" / "card_1024x1536.png")
    out_png = Path(args.out_png) if args.out_png else None

    # Also ensure watermark.svg exists (for storage + verification)
    svg_path = card_dir / "watermark.svg"
    if not svg_path.exists():
        # Import locally to avoid circular import issues
        from watermark import build_svg

        identity = _load_card_identity(card_dir)
        payload = _canonical_payload(identity)
        sig_hex = compute_signature_hex(payload)
        svg = build_svg(sig_hex=sig_hex, payload=payload, size_px=int(args.size))
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg)

    out_path = apply_watermark(
        card_dir=card_dir,
        in_png=in_png,
        out_png=out_png,
        size_px=int(args.size),
        inset_px=int(args.inset),
    )

    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
