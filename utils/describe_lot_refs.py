#!/usr/bin/env python3
"""One-time utility to describe LOT style reference images.

Sends the style reference images to gemini-3-pro-preview and asks it to
describe exactly what it sees. This helps establish what "correct" looks like.

Usage:
    python utils/describe_lot_refs.py
"""

import os
import sys
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-genai package required. Install with: pip install google-genai")
    sys.exit(1)

# Paths
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
LOT_REFS_DIR = TEMPLATES_DIR / "lots"

MODEL = "gemini-3-pro-preview"


def read_image_bytes(path: Path) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def image_part_from_bytes(img_bytes: bytes):
    """Create a Gemini Part from image bytes."""
    if hasattr(types.Part, "from_bytes"):
        try:
            return types.Part.from_bytes(data=img_bytes, mime_type="image/png")
        except Exception:
            pass

    if hasattr(types.Part, "from_image"):
        try:
            return types.Part.from_image(image=img_bytes, mime_type="image/png")
        except Exception:
            pass

    blob_cls = getattr(types, "Blob", None)
    if blob_cls:
        return types.Part(inline_data=blob_cls(data=img_bytes, mime_type="image/png"))
    else:
        return types.Part(inline_data={"mime_type": "image/png", "data": img_bytes})


def main():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_TEXT_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY env var not set")
        return 1

    # Find reference images
    if not LOT_REFS_DIR.exists():
        print(f"Error: LOT refs directory not found: {LOT_REFS_DIR}")
        return 1

    ref_images = sorted(LOT_REFS_DIR.glob("*.png"))
    if not ref_images:
        print(f"No PNG files found in {LOT_REFS_DIR}")
        return 1

    print(f"Found {len(ref_images)} reference image(s):")
    for img in ref_images:
        print(f"  - {img.name}")
    print()

    client = genai.Client(api_key=api_key)

    # Build image parts
    image_parts = []
    for img_path in ref_images:
        print(f"Loading {img_path.name}...")
        img_bytes = read_image_bytes(img_path)
        image_parts.append(image_part_from_bytes(img_bytes))

    prompt = """Examine these LOT card reference images carefully. Describe EXACTLY what you see on each card.

For each card, describe:

1. **HEADER AREA (top)**
   - What badges/labels are in the top-left corner?
   - What badges/labels are in the top-right corner?
   - What exact text do they contain?

2. **TITLE SECTION**
   - What is the main title text?
   - Is there a subtitle? What does it say?
   - What font style/size?

3. **REWARD BANNER**
   - What color is the banner?
   - What exact text appears on it?
   - Are there multiple lines?

4. **COMPOSITION SECTION**
   - How are card type requirements shown?
   - Are there icons? What do they look like?
   - Is there any text with brackets [ ] or without?

5. **CONTEXT SECTION**
   - Where is the educational/flavor text?
   - How is it formatted?

6. **FOOTER**
   - What appears at the bottom left?
   - What appears at the bottom right?

7. **OVERALL STYLING**
   - What colors are used (be specific with hex if possible)?
   - What is the frame/border style?
   - Any decorative elements?

Be extremely precise - I will use this to grade other cards for consistency."""

    print(f"\nSending to {MODEL}...")
    print("=" * 60)

    contents = [*image_parts, types.Part.from_text(text=prompt)]

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
        )
    except Exception as e:
        print(f"API Error: {e}")
        return 1

    if not response.candidates:
        print("No response received")
        return 1

    candidate = response.candidates[0]
    parts = (candidate.content.parts if candidate.content and candidate.content.parts else [])

    for part in parts:
        if hasattr(part, "text") and part.text:
            print(part.text)

    print("=" * 60)

    # Save to file
    output_path = LOT_REFS_DIR / "reference_description.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"LOT Card Reference Description\n")
        f.write(f"Generated using {MODEL}\n")
        f.write(f"Images: {', '.join(img.name for img in ref_images)}\n")
        f.write("=" * 60 + "\n\n")
        for part in parts:
            if hasattr(part, "text") and part.text:
                f.write(part.text)

    print(f"\nSaved to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
