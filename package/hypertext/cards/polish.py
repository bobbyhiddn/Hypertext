#!/usr/bin/env python3
"""
Polish tool to remove lingering brackets from generated cards.
"""
import argparse
import os
import sys

from hypertext.cards.clean import clean_template


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove brackets from generated card image")
    parser.add_argument("in_path", help="Input image path")
    parser.add_argument("out_path", nargs="?", help="Output image path (defaults to overwrite input)")

    args = parser.parse_args()
    in_path = args.in_path
    out_path = args.out_path or in_path

    if not os.path.exists(in_path):
        print(f"Error: {in_path} not found.")
        return 1

    prompt = (
        "You are a copy machine. Reproduce this trading card EXACTLY, pixel-perfect, with one exception: "
        "if you see square brackets [ ] around any text, redraw that text without the brackets.\n\n"
        "RULES:\n"
        "1. Copy the ENTIRE card exactly - frame, artwork, all text, all icons\n"
        "2. If text says '[WORD]', write 'WORD' instead (no brackets)\n"
        "3. If text says '[RARE]', write 'RARE' instead (no brackets)\n"
        "4. ALL words inside brackets MUST appear in the output, just without the [ ] characters\n"
        "5. If there are no brackets, output the image completely unchanged\n\n"
        "The stat pips, rarity diamond, artwork, and layout must be identical to the input."
    )

    print(f"Polishing card (removing brackets) -> {out_path}...")
    try:
        clean_template(
            in_path,
            out_path,
            prompt=prompt,
            model=os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3-pro-image-preview"),
            image_size="2K",
            max_attempts=3,
            base_delay_s=2.0,
            timeout_s=180.0
        )
        print("Polish complete.")
    except Exception as e:
        print(f"Error polishing card: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
