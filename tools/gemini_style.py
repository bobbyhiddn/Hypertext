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
    if genai is None:
        raise RuntimeError("google-genai package not found. Install with: pip install google-genai")

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_TEXT_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY (or GEMINI_TEXT_API_KEY) env var is not set.")

    client = genai.Client(api_key=api_key)

    # Read style image
    style_bytes = _read_image_bytes(style_image_path)
    
    # Create the prompt with reference placeholder
    # Pattern: "Generate an image in style [1] based on: {prompt}"
    full_prompt = f"Generate an image in style [1] based on: {prompt_text}"
    
    # Construct contents
    # We try multiple ways to construct the image part since the SDK is evolving
    image_part = None
    
    # Try 1: types.Part.from_bytes (newer SDKs)
    if hasattr(types.Part, "from_bytes"):
        try:
            image_part = types.Part.from_bytes(data=style_bytes, mime_type="image/png")
        except Exception:
            pass
            
    # Try 2: types.Part.from_image (some versions)
    if image_part is None and hasattr(types.Part, "from_image"):
        try:
            image_part = types.Part.from_image(image=style_bytes, mime_type="image/png")
        except Exception:
            pass

    # Try 3: Direct construction with Blob/InlineData (older/raw SDKs)
    if image_part is None:
        try:
            # Check for Blob or InlineData types
            blob_cls = getattr(types, "Blob", None)
            if blob_cls:
                image_part = types.Part(inline_data=blob_cls(data=style_bytes, mime_type="image/png"))
            else:
                # Fallback to base64 encoding manual construction if needed, 
                # but typically one of the above works. 
                # Let's try raw dictionary/object construction as a last resort wrapper
                image_part = types.Part(
                    inline_data={"mime_type": "image/png", "data": style_bytes}
                )
        except Exception as e:
            raise RuntimeError(f"Failed to construct image part. SDK version might be incompatible. Error: {e}")

    contents = [
        image_part,
        types.Part.from_text(text=full_prompt),
    ]

    print(f"Generating with style reference: {style_image_path}")
    print(f"Prompt: {full_prompt}")

    # Config parameters
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
    )
    
    # Add optional generation parameters if supported by the SDK version
    # Note: exact parameter names for image generation in the Python SDK can vary by version
    # We'll stick to the basic config for now to ensure compatibility
    
    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )
    except Exception as e:
        raise RuntimeError(f"Gemini API request failed: {e}")

    # Extract image from response
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
        # Fallback: check if it's base64 encoded string in the part text (rare but possible in some error modes)
        raise RuntimeError(f"No image data found in response. Content: {candidate.content}")

    # Decode if it's already bytes (the SDK might return bytes or b64 string depending on version)
    if isinstance(image_bytes, str):
        image_bytes = base64.b64decode(image_bytes)

    # Save output
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(image_bytes)
    
    print(f"Saved generated image to: {out_path}")

def main() -> int:
    parser = argparse.ArgumentParser(description="Generate image with Gemini Style Reference")
    parser.add_argument("--prompt", help="Text description of the image content")
    parser.add_argument("--prompt-file", help="Path to text file containing the prompt")
    parser.add_argument("--style", required=True, help="Path to reference style image")
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
        generate_with_style(
            prompt_text=prompt_text,
            style_image_path=args.style,
            out_path=args.out,
            model=args.model,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
        
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
