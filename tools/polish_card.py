#!/usr/bin/env python3
"""
Polish tool to remove lingering brackets from generated cards.
"""
import argparse
import os
import sys
from clean_card_template import clean_template

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
        "Reproduce this trading card image EXACTLY as shown, with ONE small change: "
        "remove any square bracket characters '[' or ']' that appear around text. "
        "\n\n"
        "IMPORTANT - What you MUST do:\n"
        "- Output the COMPLETE card with ALL text, artwork, and design intact\n"
        "- Keep every word, every letter, every piece of text that appears on the card\n"
        "- The title text, definition text, ability text, and rarity label must ALL remain\n"
        "- Only delete the bracket symbols themselves, nothing else\n"
        "\n"
        "Examples:\n"
        "- '[Arcane Whisper]' becomes 'Arcane Whisper' (keep the words, remove only [ and ])\n"
        "- '[RARE]' becomes 'RARE' (keep RARE, remove only [ and ])\n"
        "- 'A mystical force [flows]' becomes 'A mystical force flows'\n"
        "\n"
        "If there are NO brackets in the image, output the image unchanged.\n"
        "Do NOT leave blank spaces where text was. The text must remain readable."
    )

    print(f"Polishing card (removing brackets) -> {out_path}...")
    try:
        clean_template(
            in_path, 
            out_path, 
            prompt=prompt,
            model=os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image"),
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
