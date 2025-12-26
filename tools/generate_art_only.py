#!/usr/bin/env python3
"""
Generate art-only images for Hypertext cards.

This generates ONLY the illustration (no card frame, no text, no UI elements)
to be composited into the card template.
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateImage"

# Art panel dimensions (slightly larger for quality, will be resized)
ART_WIDTH = 1024
ART_HEIGHT = 400  # Matches the art panel aspect ratio roughly


def generate_art_only(
    art_prompt: str,
    out_path: str,
    *,
    aspect_ratio: str = "5:2",  # Wide aspect for art panel
    max_attempts: int = 6,
    base_delay_s: float = 2.0,
    timeout_s: float = 120.0,
) -> None:
    """
    Generate art-only image from a prompt.
    
    The prompt should describe ONLY the scene/illustration, with no references
    to card frames, text, or UI elements.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_TEXT_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY (or GEMINI_TEXT_API_KEY) env var is not set.")

    # Wrap the art prompt to ensure no card elements
    full_prompt = (
        f"Generate a single illustration for a trading card. "
        f"Art description: {art_prompt}\n\n"
        f"CRITICAL RULES:\n"
        f"- Output ONLY the artwork/illustration itself\n"
        f"- NO card frame, border, or UI elements\n"
        f"- NO text, labels, titles, or captions\n"
        f"- NO card template elements\n"
        f"- Fill the entire image with the scene\n"
        f"- Style: painterly, antique, warm parchment-friendly tones\n"
        f"- No modern objects or anachronisms\n"
    )

    # Try the newer image generation endpoint first
    endpoints = [
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateImage",
        "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-preview-image-generation:generateContent",
    ]

    # Use the standard generateContent endpoint with image output
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
    
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
        },
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )

    last_error = None
    data = None

    for attempt in range(1, max_attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                raw = resp.read().decode("utf-8")
                data = json.loads(raw)
            last_error = None
            break
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            
            if e.code in (429, 500, 502, 503, 504) and attempt < max_attempts:
                delay = base_delay_s * (2 ** (attempt - 1))
                print(f"Gemini request failed with HTTP {e.code}. Retrying in {delay:.1f}s...", file=sys.stderr)
                time.sleep(delay)
                last_error = e
                continue
            
            raise RuntimeError(f"Gemini request failed: HTTP {e.code}\n{body[:500]}") from e
        except urllib.error.URLError as e:
            if attempt < max_attempts:
                delay = base_delay_s * (2 ** (attempt - 1))
                print(f"URL error: {e}. Retrying in {delay:.1f}s...", file=sys.stderr)
                time.sleep(delay)
                last_error = e
                continue
            raise

    if last_error is not None or data is None:
        raise RuntimeError("Gemini request failed after retries.") from last_error

    # Extract image from response
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"No candidates returned. Response: {str(data)[:500]}")

    parts = candidates[0].get("content", {}).get("parts", [])
    image_b64 = None
    for p in parts:
        inline = p.get("inlineData")
        if inline and inline.get("mimeType", "").startswith("image/"):
            image_b64 = inline.get("data")
            break

    if not image_b64:
        raise RuntimeError(f"No image data found in response: {str(data)[:500]}")

    img_bytes = base64.b64decode(image_b64)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(img_bytes)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate art-only image for card compositing")
    parser.add_argument("--prompt", required=True, help="Art description prompt")
    parser.add_argument("--out", required=True, help="Output PNG path")
    parser.add_argument("--prompt-file", help="Read prompt from file instead of --prompt")
    
    args = parser.parse_args()
    
    prompt = args.prompt
    if args.prompt_file and os.path.exists(args.prompt_file):
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read().strip()
    
    generate_art_only(prompt, args.out)
    print(f"Generated: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
