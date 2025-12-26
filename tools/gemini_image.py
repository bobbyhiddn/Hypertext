#!/usr/bin/env python3
import base64
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent"


def _parse_retry_after_seconds(headers) -> int | None:
    if not headers:
        return None
    value = headers.get("Retry-After")
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _read_http_error_body(e: urllib.error.HTTPError) -> str:
    try:
        body = e.read()
    except Exception:
        return ""
    try:
        return body.decode("utf-8", errors="replace")
    except Exception:
        return ""


def generate_image(
    prompt: str,
    out_path: str,
    *,
    aspect_ratio: str = "2:3",
    image_size: str = "2K",
) -> None:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_TEXT_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY (or GEMINI_TEXT_API_KEY) env var is not set.")

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

    max_attempts = int(os.environ.get("GEMINI_MAX_ATTEMPTS", "6"))
    base_delay_s = float(os.environ.get("GEMINI_RETRY_BASE_DELAY_S", "2"))
    timeout_s = float(os.environ.get("GEMINI_HTTP_TIMEOUT_S", "120"))

    last_error: Exception | None = None
    raw = ""
    data: dict | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                raw = resp.read().decode("utf-8")
                data = json.loads(raw)
            last_error = None
            break
        except urllib.error.HTTPError as e:
            body = _read_http_error_body(e)
            retry_after = _parse_retry_after_seconds(getattr(e, "headers", None))
            retriable = e.code in (429, 500, 502, 503, 504)

            if retriable and attempt < max_attempts:
                delay = retry_after if retry_after is not None else (base_delay_s * (2 ** (attempt - 1)))
                delay = delay + random.random()
                print(
                    f"Gemini request failed with HTTP {e.code}. Retrying in {delay:.1f}s (attempt {attempt}/{max_attempts}).",
                    file=sys.stderr,
                )
                if body:
                    print(f"Gemini error body (truncated): {body[:800]}", file=sys.stderr)
                time.sleep(delay)
                last_error = e
                continue

            msg = f"Gemini request failed with HTTP {e.code}: {e.reason}"
            if body:
                msg += f"\nBody (truncated): {body[:2000]}"
            raise RuntimeError(msg) from e
        except urllib.error.URLError as e:
            if attempt < max_attempts:
                delay = base_delay_s * (2 ** (attempt - 1)) + random.random()
                print(
                    f"Gemini request failed with URLError: {e}. Retrying in {delay:.1f}s (attempt {attempt}/{max_attempts}).",
                    file=sys.stderr,
                )
                time.sleep(delay)
                last_error = e
                continue
            raise

    if last_error is not None or data is None:
        raise RuntimeError("Gemini request failed after retries.") from last_error

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
