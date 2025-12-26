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
        "The image is a trading card. Your task is to remove typographic square brackets '[ ]' from the text fields. "
        "CRITICAL RULES: "
        "1. Detect any text enclosed in brackets, such as '[Some Text]'. "
        "2. Erase ONLY the brackets '[' and ']' by filling them with the background color. "
        "3. YOU MUST PRESERVE THE TEXT INSIDE. Do NOT delete the words. "
        "   - CORRECT: '[Title]' -> 'Title' "
        "   - WRONG:   '[Title]' -> '' (Empty space) "
        "4. If the text is the definition/gloss under the title, keep the definition words exactly as they are. "
        "5. Do not change any other part of the card. "
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
