#!/usr/bin/env python3
"""Test script to debug style mismatch detection.

Sends the style reference images AND a test card to Gemini and asks it
to compare styles and identify differences.

Usage:
    python utils/test_style_detection.py
    python utils/test_style_detection.py --card series/2026-Q1/lots/05-scroll/outputs/lot_1024x1536.png
"""

import argparse
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
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
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
    parser = argparse.ArgumentParser(description="Test style mismatch detection")
    parser.add_argument(
        "--card",
        default="series/2026-Q1/lots/05-scroll/outputs/lot_1024x1536.png",
        help="Path to card image to test"
    )
    args = parser.parse_args()

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

    # Find test card
    card_path = PROJECT_ROOT / args.card
    if not card_path.exists():
        card_path = Path(args.card)
    if not card_path.exists():
        print(f"Error: Card not found: {args.card}")
        return 1

    print(f"Reference images ({len(ref_images)}):")
    for img in ref_images:
        print(f"  [REF] {img.name}")
    print(f"\nTest card:")
    print(f"  [TEST] {card_path.name}")
    print()

    client = genai.Client(api_key=api_key)

    # Build image parts - refs first, then test card
    image_parts = []
    labels = []

    for i, img_path in enumerate(ref_images, 1):
        print(f"Loading ref {i}: {img_path.name}...")
        img_bytes = read_image_bytes(img_path)
        image_parts.append(image_part_from_bytes(img_bytes))
        labels.append(f"[{i}] REFERENCE: {img_path.name}")

    test_idx = len(ref_images) + 1
    print(f"Loading test card: {card_path.name}...")
    test_bytes = read_image_bytes(card_path)
    image_parts.append(image_part_from_bytes(test_bytes))
    labels.append(f"[{test_idx}] TEST CARD: {card_path.name}")

    labels_text = "\n".join(labels)

    prompt = f"""You are provided with reference LOT card images and one test card to evaluate.

IMAGE LABELS:
{labels_text}

## TASK 1: Describe the REFERENCE style

Look at images [1] through [{len(ref_images)}]. These are the CORRECT reference style.
Describe the visual style in detail:
- Background texture and color
- Color palette (what colors are used for UI elements?)
- Layout structure (badges, banners, panels, borders)
- Typography style
- Overall aesthetic (antique? modern? cartoon? photorealistic?)

## TASK 2: Describe the TEST card style

Look at image [{test_idx}]. This is the card being evaluated.
Describe its visual style using the same criteria.

## TASK 3: Compare and determine if styles match

Answer these questions:
1. Does the test card have the same background texture as the references?
2. Does the test card use the same color palette (navy/gold/parchment)?
3. Does the test card have the same structured layout (badges, banners, panels)?
4. Does the test card have the same typography feel?
5. Does the test card have the same overall aesthetic?

## TASK 4: Final verdict

Based on your comparison, answer:
- STYLE_MATCHES_REFERENCE: true or false?
- If false, explain specifically what is different.

Be VERY strict. If the test card looks like a different art style, different color scheme,
or different layout structure, it is a STYLE MISMATCH (false).

A card that shows a scene, illustration, or artistic rendering instead of a structured
card layout with UI elements is a STYLE MISMATCH.
"""

    print(f"\nSending to {MODEL}...")
    print("=" * 70)

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

    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
