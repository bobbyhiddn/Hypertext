#!/usr/bin/env python3
"""
One-time utility to remove brackets from the card number in the top left of the template.
"""
import os
import sys
from clean_card_template import clean_template


def main():
    in_path = os.path.join("tools", "clean_template_final.png")
    out_path = os.path.join("tools", "clean_template_final.png")  # Overwrite

    if not os.path.exists(in_path):
        print(f"Error: {in_path} not found.")
        return 1

    prompt = "Remove the brackets from the card number in the top left corner of this template. Keep everything else exactly the same."

    print(f"Cleaning card number brackets in {in_path}...")
    try:
        clean_template(
            in_path,
            out_path,
            prompt=prompt,
            model=os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3-pro-image-preview"),
            image_size="2K",
            max_attempts=6,
            base_delay_s=2.0,
            timeout_s=180.0,
        )
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
