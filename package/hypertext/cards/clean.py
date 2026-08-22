#!/usr/bin/env python3
"""Clean card template using Gemini image editing."""

import argparse
import os
import random
import sys
import time

from hypertext.gemini.config import image_model
from hypertext.gemini.image_contract import (
    MAX_ATTEMPTS, ImageContractError, atomic_write_image, classify_error,
    decode_and_validate, record_failure, record_success, validate_request,
)

try:
    from google import genai
    from google.genai import types
except Exception as e:  # pragma: no cover
    genai = None
    types = None
    _IMPORT_ERROR = e


def _text_part(text: str):
    fn = getattr(types.Part, "from_text", None)
    if callable(fn):
        return fn(text=text)
    return types.Part(text=text)


def _generate_edit_response(*, client, model: str, prompt: str, image_part,
                            image_size: str):
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="2:3", image_size=image_size),
    )
    return client.models.generate_content(
        model=model, contents=[_text_part(prompt), image_part], config=config,
    )

def clean_template(
    in_path: str,
    out_path: str,
    *,
    prompt: str,
    model: str,
    image_size: str,
    max_attempts: int,
    base_delay_s: float,
    timeout_s: float,
) -> None:
    if genai is None or types is None:
        raise RuntimeError(
            "Missing dependency: google-genai. Install it with: pip install google-genai\n"
            f"Import error: {_IMPORT_ERROR}"
        )

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_TEXT_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY (or GEMINI_TEXT_API_KEY) env var is not set.")

    with open(in_path, "rb") as f:
        img_bytes = f.read()

    validate_request("2:3", image_size)
    client = genai.Client(api_key=api_key)

    image_part = types.Part.from_bytes(data=img_bytes, mime_type="image/png")

    max_attempts = min(MAX_ATTEMPTS, max(1, max_attempts))
    for attempt in range(1, max_attempts + 1):
        try:
            request_started = time.monotonic()
            resp = _generate_edit_response(client=client, model=model, prompt=prompt,
                                           image_part=image_part, image_size=image_size)
            latency_ms = round((time.monotonic() - request_started) * 1000)
            break
        except Exception as e:
            category, status, retriable = classify_error(e)
            if not retriable or attempt == max_attempts:
                record_failure(out_path, model=model, category=category, attempts=attempt,
                               reference_count=1, status_code=status)
                raise RuntimeError(f"Gemini API request failed: {e}") from e
            time.sleep(base_delay_s * (2 ** (attempt - 1)) + random.random())

    out_bytes: bytes | None = None
    parts = getattr(resp, "parts", None)
    if parts is None and getattr(resp, "candidates", None):
        try:
            parts = resp.candidates[0].content.parts
        except Exception:
            parts = None

    if not parts:
        record_failure(out_path, model=model, category="no_candidate", attempts=attempt,
                       reference_count=1)
        raise RuntimeError("No image parts returned from Gemini")

    for part in parts:
        inline = getattr(part, "inline_data", None)
        if inline is None:
            inline = getattr(part, "inlineData", None)
        if inline is None:
            continue

        data = getattr(inline, "data", None)
        mime_type = getattr(inline, "mime_type", getattr(inline, "mimeType", ""))
        if data is None:
            continue
        out_bytes = data
        break

    if not out_bytes:
        record_failure(out_path, model=model, category="missing_image", attempts=attempt,
                       reference_count=1)
        raise RuntimeError("No image inline_data found in Gemini response")
    try:
        out_bytes, dimensions = decode_and_validate(out_bytes, mime_type)
    except ImageContractError:
        record_failure(out_path, model=model, category="image_contract", attempts=attempt,
                       reference_count=1)
        raise
    atomic_write_image(out_path, out_bytes)
    usage = getattr(resp, "usage_metadata", None)
    if usage is not None and hasattr(usage, "model_dump"):
        usage = usage.model_dump(exclude_none=True)
    record_success(out_path, model=model, mime_type=mime_type, dimensions=dimensions,
                   attempts=attempt, reference_count=1, latency_ms=latency_ms,
                   usage_metadata=usage if isinstance(usage, dict) else None)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", default=str(os.path.join("tools", "raw_template.png")))
    parser.add_argument("--out", dest="out_path", default=str(os.path.join("templates", "blank_template.png")))
    parser.add_argument("--model", default=image_model())
    parser.add_argument("--image-size", default=os.environ.get("GEMINI_IMAGE_SIZE", "2K"))
    parser.add_argument("--max-attempts", type=int, default=int(os.environ.get("GEMINI_MAX_ATTEMPTS", str(MAX_ATTEMPTS))))
    parser.add_argument("--retry-base-delay-s", type=float, default=float(os.environ.get("GEMINI_RETRY_BASE_DELAY_S", "2")))
    parser.add_argument("--timeout-s", type=float, default=float(os.environ.get("GEMINI_HTTP_TIMEOUT_S", "180")))
    parser.add_argument(
        "--prompt",
        default=(
            "The image is a trading card template. You are cleaning up formatting artifacts. "
            "Output the exact same image, but with the following corrections: "
            "1. Remove the square brackets '[ ]' around the Rarity text in the top right (e.g. '[RARITY]'). Keep the text 'RARITY' (or whatever text is inside) but delete the brackets. "
            "2. Remove any parentheses '( )' around text. Keep the text inside but delete the parentheses. "
            "3. Ensure NO other brackets or parentheses exist in the image. "
            "CRITICAL: "
            "- Do NOT remove the Rarity icon (the diamond/shape next to the text). "
            "- Do NOT change the card frame or other text. "
            "- The goal is just to delete the square brackets and parentheses around text."
        ),
    )

    args = parser.parse_args()

    try:
        clean_template(
            args.in_path,
            args.out_path,
            prompt=args.prompt,
            model=args.model,
            image_size=args.image_size,
            max_attempts=args.max_attempts,
            base_delay_s=args.retry_base_delay_s,
            timeout_s=args.timeout_s,
        )
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1

    print(args.out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
