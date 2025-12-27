#!/usr/bin/env python3
"""
Generate images using Gemini 3 Pro with Style Reference.

This script implements the Gemini Style Reference API pattern to generate
images that follow the visual style of a provided reference image.
"""
import argparse
import base64
import os
import sys
import time
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

def generate_with_styles(
    prompt_text: str,
    style_image_paths: list[str],
    out_path: str,
    *,
    model: str = "gemini-3-pro-preview",
    aspect_ratio: str = "2:3",
    guidance_scale: float | None = None,
    num_inference_steps: int | None = None,
) -> None:
    if genai is None:
        raise RuntimeError("google-genai package not found. Install with: pip install google-genai")

    if not style_image_paths:
        raise RuntimeError("At least one style image is required.")
    if len(style_image_paths) > 16:
        raise RuntimeError("At most 16 style images are supported.")

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_TEXT_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY (or GEMINI_TEXT_API_KEY) env var is not set.")

    client = genai.Client(api_key=api_key)

    orientation = "portrait (2:3 aspect ratio, taller than wide)" if aspect_ratio == "2:3" else f"aspect ratio {aspect_ratio}"
    
    # Build clear labeling for each reference image
    ref_labels = []
    ref_labels.append("[1] = Clean template (layout/frame reference)")
    for i in range(2, len(style_image_paths) + 1):
        ref_labels.append(f"[{i}] = Example card (style/formatting reference)")
    
    # Remove conflicting "[1]" reference from prompt if present
    cleaned_prompt = prompt_text.replace(
        "Generate a trading card following the EXACT layout, frame, and geometry of the reference style [1].",
        ""
    ).strip()
    
    example_refs = "/".join(str(i) for i in range(2, len(style_image_paths) + 1)) if len(style_image_paths) > 1 else "1"
    
    style_instruction = (
        f"You are provided {len(style_image_paths)} reference images:\n"
        + "\n".join(ref_labels) + "\n\n"
        f"Generate a {orientation} trading card that EXACTLY matches:\n"
        f"- The layout and frame structure from [1] (template)\n"
        f"- The corner styles, stat pip style (navy circles), rarity badge style, and text formatting from [{example_refs}] (example cards)\n\n"
        f"CRITICAL: Copy the exact visual style of the example cards [{example_refs}] for all UI elements.\n\n"
    )
    
    full_prompt = style_instruction + cleaned_prompt

    image_parts = []
    for p in style_image_paths:
        img_bytes = _read_image_bytes(p)
        image_parts.append(_image_part_from_bytes(img_bytes))

    contents = [
        *image_parts,
        types.Part.from_text(text=full_prompt),
    ]

    print("Generating with style references:")
    for p in style_image_paths:
        print(f"- {p}")
    print(f"Prompt: {full_prompt}")

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

    print(f"Saved generated image to: {out_path}")

def generate_with_style(
    prompt_text: str,
    style_image_path: str,
    out_path: str,
    *,
    model: str = "gemini-3-pro-preview",
    aspect_ratio: str = "2:3",
    guidance_scale: float | None = None,
    num_inference_steps: int | None = None,
) -> None:
    generate_with_styles(
        prompt_text=prompt_text,
        style_image_paths=[style_image_path],
        out_path=out_path,
        model=model,
        aspect_ratio=aspect_ratio,
        guidance_scale=guidance_scale,
        num_inference_steps=num_inference_steps,
    )

def main() -> int:
    parser = argparse.ArgumentParser(description="Generate image with Gemini Style Reference")
    parser.add_argument("--prompt", help="Text description of the image content")
    parser.add_argument("--prompt-file", help="Path to text file containing the prompt")
    parser.add_argument("--style", required=True, action="append", help="Path to reference style image (repeatable)")
    parser.add_argument("--out", required=True, help="Output PNG path")
    parser.add_argument("--model", default="gemini-3-pro-image-preview", help="Gemini model ID")
    
    args = parser.parse_args()
    
    prompt_text = args.prompt
    if args.prompt_file:
        if not os.path.exists(args.prompt_file):
            print(f"Error: Prompt file not found: {args.prompt_file}", file=sys.stderr)
            return 1
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompt_text = f.read().strip()
            
    if not prompt_text:
        print("Error: Must provide either --prompt or --prompt-file", file=sys.stderr)
        return 1
    
    try:
        generate_with_styles(
            prompt_text=prompt_text,
            style_image_paths=args.style,
            out_path=args.out,
            model=args.model,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
        
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
