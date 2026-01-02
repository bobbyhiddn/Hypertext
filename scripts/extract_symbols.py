#!/usr/bin/env python3
"""Extract symbol palettes from template images using Gemini.

This script uses the google-genai SDK (same as the package) to extract
and generate clean symbol palette images from the lot template.

Usage:
    python scripts/extract_symbols.py
"""

import base64
import os
import sys
from pathlib import Path

# Add package to path for consistent imports
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "package"))

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

# Paths
LOT_TEMPLATE = REPO_ROOT / "templates" / "lot" / "v001" / "base" / "template_1024x1536.png"
OUTPUT_DIR = REPO_ROOT / "templates" / "palettes"

# Model (same as package/hypertext/gemini/style.py)
MODEL = "gemini-3-pro-image-preview"


def _read_image_bytes(path: Path) -> bytes:
    """Read image file as bytes."""
    with open(path, "rb") as f:
        return f.read()


def _image_part_from_bytes(img_bytes: bytes):
    """Create a Gemini Part from image bytes with SDK compatibility fallbacks."""
    if types is None:
        raise RuntimeError("google-genai package not found. Install with: pip install google-genai")

    image_part = None

    if hasattr(types.Part, "from_bytes"):
        try:
            image_part = types.Part.from_bytes(data=img_bytes, mime_type="image/png")
        except Exception:
            pass

    if image_part is None and hasattr(types.Part, "from_image"):
        try:
            image_part = types.Part.from_image(image=img_bytes, mime_type="image/png")
        except Exception:
            pass

    if image_part is None:
        try:
            blob_cls = getattr(types, "Blob", None)
            if blob_cls:
                image_part = types.Part(inline_data=blob_cls(data=img_bytes, mime_type="image/png"))
            else:
                image_part = types.Part(
                    inline_data={"mime_type": "image/png", "data": img_bytes}
                )
        except Exception as e:
            raise RuntimeError(f"Failed to construct image part. SDK version might be incompatible. Error: {e}")

    return image_part


def generate_from_reference(
    prompt: str,
    reference_image_path: Path,
    out_path: Path,
) -> bool:
    """Generate an image using a reference image and prompt.

    Unlike generate_with_styles(), this does NOT add layout-preservation
    instructions - it sends the prompt as-is with the reference image.
    """
    if genai is None:
        print("Error: google-genai package not found. Install with: pip install google-genai")
        return False

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_TEXT_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        return False

    client = genai.Client(api_key=api_key)

    # Build contents: image + text prompt
    img_bytes = _read_image_bytes(reference_image_path)
    image_part = _image_part_from_bytes(img_bytes)
    text_part = types.Part.from_text(text=prompt)

    contents = [image_part, text_part]

    # Note: image.py uses ["TEXT", "IMAGE"], style.py uses ["IMAGE"]
    # Try with both to see if that helps
    config = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
    )

    print(f"  Generating with model: {MODEL}")
    print(f"  Prompt: {prompt[:200]}...")

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=config,
        )
    except Exception as e:
        print(f"  API request failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Debug: print full response structure
    print(f"  Response: {response}")

    if not response.candidates:
        print("  No candidates returned from Gemini.")
        # Check for prompt feedback
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            print(f"  Prompt feedback: {response.prompt_feedback}")
        return False

    candidate = response.candidates[0]
    parts = (candidate.content.parts if candidate.content and candidate.content.parts else [])

    image_bytes = None
    for part in parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            image_bytes = part.inline_data.data
            break

    if not image_bytes:
        # Check for text response
        for part in parts:
            if hasattr(part, 'text') and part.text:
                print(f"  No image generated. Model response: {part.text[:300]}")
                break
        else:
            print(f"  No image data found in response. Content: {candidate.content}")
        return False

    if isinstance(image_bytes, str):
        image_bytes = base64.b64decode(image_bytes)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(image_bytes)

    return True


def extract_type_symbols():
    """Use Gemini to extract type symbols from the lot template."""
    if not LOT_TEMPLATE.exists():
        print(f"Error: Lot template not found: {LOT_TEMPLATE}")
        return False

    prompt = """Look at this lot card template image. It contains a composition row with 5 type icons.

Extract and recreate ONLY those 5 type symbol icons in a clean horizontal strip:

The 5 icons are (from left to right):
1. Book icon = NOUN
2. Pencil icon = VERB
3. Sparkle pen icon = ADJECTIVE
4. Feather quill icon = NAME
5. Framed picture icon = TITLE

GENERATE a new image that shows:
- ONLY these 5 icons in a horizontal row
- Same icon style as the source (simple line art, navy blue)
- Clean parchment/beige background (#F3E7C8)
- Even spacing between icons
- Small labels below each: [NOUN] [VERB] [ADJECTIVE] [NAME] [TITLE]
- Labels in navy blue (#0B1F3B)

Do NOT include any other elements from the template - ONLY the 5 type icons with labels.
Output a landscape-oriented image."""

    out_path = OUTPUT_DIR / "type_symbols_palette.png"

    print("Extracting type symbols from lot template...")
    print(f"  Reference: {LOT_TEMPLATE}")
    print(f"  Output: {out_path}")

    if generate_from_reference(prompt, LOT_TEMPLATE, out_path):
        print(f"  Success! Saved to: {out_path}")
        return True
    else:
        print("  Failed to extract type symbols")
        return False


def create_rarity_diamonds():
    """Use Gemini to create rarity diamond indicators."""
    prompt = """Look at this template image for color and style reference only.

Generate a NEW image showing 4 rarity indicator diamonds in a horizontal row:

1. COMMON - HOLLOW diamond (navy outline only, empty inside showing background)
2. UNCOMMON - FILLED green diamond (#2E8B57)
3. RARE - FILLED gold diamond (#C9A44C)
4. GLORIOUS - FILLED orange diamond (#F28C28)

SPECIFICATIONS:
- All 4 shapes must be DIAMOND shapes (◇ - rotated square, point at top)
- Each diamond approximately 50-60 pixels tall
- Navy blue outlines (#0B1F3B) on all diamonds
- Parchment background (#F3E7C8)
- Labels below each: COMMON, UNCOMMON, RARE, GLORIOUS
- Labels in navy blue serif font
- Even spacing in a horizontal row

Generate a landscape-oriented image with just these 4 labeled diamonds."""

    out_path = OUTPUT_DIR / "rarity_diamonds_palette.png"

    print("Creating rarity diamonds palette...")
    print(f"  Output: {out_path}")

    if LOT_TEMPLATE.exists():
        if generate_from_reference(prompt, LOT_TEMPLATE, out_path):
            print(f"  Success! Saved to: {out_path}")
            return True

    print("  Failed to create rarity diamonds")
    return False


def main():
    """Extract all symbol palettes."""
    print("=" * 60)
    print("Symbol Palette Extraction using Gemini")
    print("=" * 60)
    print()

    if genai is None:
        print("Error: google-genai package not found.")
        print("Install with: pip install google-genai")
        return 1

    # Check for API key
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GEMINI_TEXT_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable not set")
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success = True

    # 1. Extract type symbols
    print("1. Type Symbols Palette")
    print("-" * 40)
    if not extract_type_symbols():
        success = False
    print()

    # 2. Create rarity diamonds
    print("2. Rarity Diamonds Palette")
    print("-" * 40)
    if not create_rarity_diamonds():
        success = False
    print()

    print("=" * 60)
    if success:
        print("All palettes created successfully!")
        print(f"Output directory: {OUTPUT_DIR}")
    else:
        print("Some extractions failed. Check errors above.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
