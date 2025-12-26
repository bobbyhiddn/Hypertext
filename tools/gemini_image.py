#!/usr/bin/env python3
import base64
import json
import os
import sys
import urllib.request

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent"


def generate_image(
    prompt: str,
    out_path: str,
    *,
    aspect_ratio: str = "2:3",
    image_size: str = "2K",
) -> None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY env var is not set.")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": aspect_ratio, "imageSize": image_size},
        },
    }

    req = urllib.request.Request(
        GEMINI_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        raw = resp.read().decode("utf-8")
        data = json.loads(raw)

    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"No candidates returned. Raw: {raw[:500]}")

    parts = candidates[0].get("content", {}).get("parts", [])
    image_b64 = None
    for p in parts:
        inline = p.get("inlineData")
        if inline and inline.get("mimeType", "").startswith("image/"):
            image_b64 = inline.get("data")
            break

    if not image_b64:
        raise RuntimeError(f"No image inlineData found. Raw: {raw[:800]}")

    img_bytes = base64.b64decode(image_b64)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(img_bytes)


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: gemini_image.py <prompt_text_file> <out_png_path>")
        return 1

    prompt_file = sys.argv[1]
    out_png = sys.argv[2]

    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt = f.read().strip()

    generate_image(prompt, out_png)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
