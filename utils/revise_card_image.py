#!/usr/bin/env python3
"""
Revise a card image using Gemini with multiple style references.

This script takes:
1. The current (incorrect) card image - labeled with revision instructions
2. The clean template
3. Example cards (Magi, Gospel, Covenant) as style references

The model sees what needs to be fixed and has correct examples to reference.
"""
import argparse
import base64
import os
import sys
import subprocess
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


def _read_image_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def _image_part_from_bytes(img_bytes: bytes):
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


def revise_card(
    current_card_path: str,
    revision_instructions: str,
    style_ref_paths: list[str],
    out_path: str,
    *,
    model: str = "gemini-3-pro-image-preview",
) -> None:
    if genai is None:
        raise RuntimeError("google-genai package not found. Install with: pip install google-genai")

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_TEXT_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY (or GEMINI_TEXT_API_KEY) env var is not set.")

    client = genai.Client(api_key=api_key)

    # Build image parts: current card first, then style refs
    current_bytes = _read_image_bytes(current_card_path)
    current_part = _image_part_from_bytes(current_bytes)

    style_parts = []
    for p in style_ref_paths:
        img_bytes = _read_image_bytes(p)
        style_parts.append(_image_part_from_bytes(img_bytes))

    # Build prompt:
    # Image [1] = current card (to fix)
    # Images [2], [3], [4], [5] = template and example cards (correct style)
    style_labels = " ".join(f"[{i}]" for i in range(2, len(style_ref_paths) + 2))
    
    prompt = (
        f"Image [1] is a trading card that needs revision. "
        f"Images {style_labels} show the correct template and example cards with proper styling.\n\n"
        f"REVISION INSTRUCTIONS:\n{revision_instructions}\n\n"
        f"Generate a corrected portrait (2:3 aspect ratio, taller than wide) version of image [1] "
        f"that applies the revision instructions while matching the style and quality of images {style_labels}. "
        f"Keep all other content from image [1] exactly the same - only fix what the instructions specify."
    )

    contents = [
        current_part,
        *style_parts,
        types.Part.from_text(text=prompt),
    ]

    print("Revising card with references:")
    print(f"[1] Current card: {current_card_path}")
    for i, p in enumerate(style_ref_paths, start=2):
        print(f"[{i}] {p}")
    print(f"\nRevision instructions: {revision_instructions}")
    print(f"Prompt: {prompt[:200]}...")

    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )
    except Exception as e:
        raise RuntimeError(f"Gemini API request failed: {e}")

    if not response.candidates:
        raise RuntimeError("No candidates returned from Gemini.")

    candidate = response.candidates[0]
    parts = candidate.content.parts if candidate.content else []

    image_bytes = None
    for part in parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            image_bytes = part.inline_data.data
            break

    if not image_bytes:
        raise RuntimeError(f"No image data found in response. Content: {candidate.content}")

    if isinstance(image_bytes, str):
        image_bytes = base64.b64decode(image_bytes)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(image_bytes)

    print(f"Saved revised card to: {out_path}")

    try:
        out_p = Path(out_path)
        # If out is .../series/<series>/cards/<card>/outputs/<file>.png, then card_dir is parent of outputs.
        if out_p.suffix.lower() == ".png" and out_p.parent.name == "outputs":
            card_dir = out_p.parent.parent
            watermark_cmd = [
                sys.executable,
                str(Path("tools") / "apply_watermark.py"),
                "--card-dir",
                str(card_dir),
                "--in",
                str(out_p),
            ]
            subprocess.check_call(watermark_cmd)
            print("Applied watermark")
    except Exception as e:
        print(f"Warning: watermark step failed: {e}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Revise a card image with style references")
    parser.add_argument("--card", required=True, help="Path to current card image to revise")
    parser.add_argument("--instructions", required=True, help="Revision instructions text")
    parser.add_argument("--style", action="append", default=[], help="Style reference image (repeatable)")
    parser.add_argument("--out", required=True, help="Output PNG path")
    parser.add_argument("--model", default="gemini-3-pro-image-preview", help="Gemini model ID")

    args = parser.parse_args()

    if not os.path.exists(args.card):
        print(f"Error: Card image not found: {args.card}", file=sys.stderr)
        return 1

    for s in args.style:
        if not os.path.exists(s):
            print(f"Error: Style reference not found: {s}", file=sys.stderr)
            return 1

    try:
        revise_card(
            current_card_path=args.card,
            revision_instructions=args.instructions,
            style_ref_paths=args.style,
            out_path=args.out,
            model=args.model,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
