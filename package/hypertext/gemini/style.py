#!/usr/bin/env python3
"""Generate images using Gemini with style references.

This module implements the Gemini Style Reference API pattern to generate
images that follow the visual style of provided reference images.
"""

import argparse
import base64
import os
import sys
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


def _read_image_bytes(path: str) -> bytes:
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


def generate_with_styles(
    prompt_text: str,
    style_image_paths: list[str],
    out_path: str,
    *,
    model: str = "gemini-3-pro-preview",
    aspect_ratio: str = "2:3",
    guidance_scale: float | None = None,
    num_inference_steps: int | None = None,
    rarity_labels: dict[int, str] | None = None,
    target_rarity: str | None = None,
    fix_mode: bool = False,
) -> None:
    """Generate an image with style references.

    Args:
        prompt_text: The text prompt describing the desired image.
        style_image_paths: List of paths to style reference images.
        out_path: Path where the generated PNG will be saved.
        model: Gemini model ID to use.
        aspect_ratio: Aspect ratio for the image (default "2:3" for cards).
        guidance_scale: Optional guidance scale parameter.
        num_inference_steps: Optional inference steps parameter.
        rarity_labels: Optional dict mapping 1-indexed image position to rarity name
                      e.g. {2: "COMMON", 3: "UNCOMMON", 4: "RARE", 5: "GLORIOUS"}
        target_rarity: Optional target rarity - the matching reference will be highlighted.
        fix_mode: If True, [1] is the card being fixed, [2] is template, [3+] are examples.
                  If False, [1] is template, [2+] are examples.

    Raises:
        RuntimeError: If the API call fails or no image is returned.
    """
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

    if fix_mode:
        # Fix mode: [1]=card to fix, [2]=template, [3+]=examples
        ref_labels.append("[1] = Card being fixed (PRESERVE this card's style, only fix specified issues)")
        ref_labels.append("[2] = Clean template (layout/frame reference)")
        example_start = 3
    else:
        # Generate mode: [1]=template, [2+]=examples
        ref_labels.append("[1] = Clean template (layout/frame reference)")
        example_start = 2

    primary_ref = None
    for i in range(example_start, len(style_image_paths) + 1):
        rarity = rarity_labels.get(i) if rarity_labels else None
        if rarity:
            is_primary = (target_rarity and rarity.upper() == target_rarity.upper())
            if is_primary:
                ref_labels.append(f"[{i}] = {rarity} example card ⭐ PRIMARY RARITY REFERENCE")
                primary_ref = i
            else:
                ref_labels.append(f"[{i}] = {rarity} example card")
        else:
            ref_labels.append(f"[{i}] = Example card (style/formatting reference)")

    # Remove conflicting "[1]" reference from prompt if present
    cleaned_prompt = prompt_text.replace(
        "Generate a trading card following the EXACT layout, frame, and geometry of the reference style [1].",
        ""
    ).strip()

    # Build example refs string based on mode
    if fix_mode:
        template_ref = "2"
        example_refs = "/".join(str(i) for i in range(3, len(style_image_paths) + 1)) if len(style_image_paths) > 2 else "2"
    else:
        template_ref = "1"
        example_refs = "/".join(str(i) for i in range(2, len(style_image_paths) + 1)) if len(style_image_paths) > 1 else "1"

    # Build primary rarity instruction if we have a match
    primary_instruction = ""
    if primary_ref and target_rarity:
        primary_instruction = (
            f"\n⭐ IMPORTANT: This card is {target_rarity} rarity. "
            f"Pay CLOSEST attention to [{primary_ref}] for the rarity badge style and any rarity-specific formatting.\n"
        )

    if fix_mode:
        style_instruction = (
            f"You are provided {len(style_image_paths)} reference images:\n"
            + "\n".join(ref_labels) + "\n\n"
            f"You are FIXING the card in [1]. Reproduce it EXACTLY with the requested corrections.\n"
            f"- PRESERVE all content, layout, artwork, and style from [1]\n"
            f"- Use [{template_ref}] for frame/layout reference\n"
            f"- Use [{example_refs}] for style consistency verification\n"
            + primary_instruction +
            f"\nCRITICAL: The output should be nearly identical to [1], with only the specified fixes applied.\n\n"
        )
    else:
        style_instruction = (
            f"You are provided {len(style_image_paths)} reference images:\n"
            + "\n".join(ref_labels) + "\n\n"
            f"Generate a {orientation} trading card that EXACTLY matches:\n"
            f"- The layout and frame structure from [{template_ref}] (template)\n"
            f"- The corner styles, stat pip style (navy circles), rarity badge style, and text formatting from [{example_refs}] (example cards)\n"
            + primary_instruction +
            f"\nCRITICAL: Copy the exact visual style of the example cards [{example_refs}] for all UI elements.\n\n"
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
    parts = (candidate.content.parts if candidate.content and candidate.content.parts else [])

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
    """Convenience wrapper for single style image."""
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
    """CLI entrypoint for style-referenced image generation."""
    parser = argparse.ArgumentParser(description="Generate image with Gemini Style Reference")
    parser.add_argument("--prompt", help="Text description of the image content")
    parser.add_argument("--prompt-file", help="Path to text file containing the prompt")
    parser.add_argument("--style", required=True, action="append", help="Path to reference style image (repeatable)")
    parser.add_argument("--out", required=True, help="Output PNG path")
    parser.add_argument("--model", default="gemini-3-pro-image-preview", help="Gemini model ID")
    parser.add_argument("--rarity-label", action="append", help="Rarity label for style image at position (format: POS:RARITY e.g. 2:COMMON)")
    parser.add_argument("--target-rarity", help="Target rarity for this card (highlights matching reference)")
    parser.add_argument("--fix-mode", action="store_true", help="Fix mode: [1]=card to fix, [2]=template, [3+]=examples")

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

    # Parse rarity labels
    rarity_labels = None
    if args.rarity_label:
        rarity_labels = {}
        for label in args.rarity_label:
            if ":" in label:
                pos, rarity = label.split(":", 1)
                rarity_labels[int(pos)] = rarity.upper()

    try:
        generate_with_styles(
            prompt_text=prompt_text,
            style_image_paths=args.style,
            out_path=args.out,
            model=args.model,
            rarity_labels=rarity_labels,
            target_rarity=args.target_rarity,
            fix_mode=args.fix_mode,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
