#!/usr/bin/env python3
import argparse
import base64
import os
import sys
import time

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
        return fn(text)
    return types.Part(text=text)


def _generate_edit_response(*, client, model: str, prompt: str, image_part):
    attempts = []

    try:
        attempts.append([_text_part(prompt), image_part])
    except Exception:
        pass

    try:
        content_cls = getattr(types, "Content", None)
        if content_cls is not None:
            attempts.append([content_cls(role="user", parts=[_text_part(prompt), image_part])])
    except Exception:
        pass

    attempts.append([prompt, image_part])

    last_error: Exception | None = None
    for contents in attempts:
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
            )
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"All Gemini request encodings failed. Last error: {last_error}") from last_error

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

    client = genai.Client(api_key=api_key)

    image_part = types.Part.from_bytes(data=img_bytes, mime_type="image/png")

    last_error: Exception | None = None
    resp = None

    for attempt in range(1, max_attempts + 1):
        try:
            resp = _generate_edit_response(client=client, model=model, prompt=prompt, image_part=image_part)
            last_error = None
            break
        except Exception as e:
            msg = str(e)
            if attempt < max_attempts:
                delay = base_delay_s * (2 ** (attempt - 1)) + (0.1 * attempt)
                print(
                    f"Gemini request failed. Retrying in {delay:.1f}s (attempt {attempt}/{max_attempts}).\n{e}",
                    file=sys.stderr,
                )
                time.sleep(delay)
                last_error = e
                continue
            raise

    if last_error is not None or resp is None:
        raise RuntimeError("Gemini request failed after retries.") from last_error

    out_bytes: bytes | None = None
    parts = getattr(resp, "parts", None)
    if parts is None and getattr(resp, "candidates", None):
        try:
            parts = resp.candidates[0].content.parts
        except Exception:
            parts = None

    if not parts:
        raise RuntimeError(f"No parts returned. Response: {resp}")

    for part in parts:
        inline = getattr(part, "inline_data", None)
        if inline is None:
            inline = getattr(part, "inlineData", None)
        if inline is None:
            continue

        data = getattr(inline, "data", None)
        if data is None:
            continue
        if isinstance(data, bytes):
            out_bytes = data
            break
        if isinstance(data, str):
            out_bytes = base64.b64decode(data)
            break

    if not out_bytes:
        raise RuntimeError(f"No image inline_data found. Response: {resp}")

    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(out_bytes)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", default=str(os.path.join("tools", "raw_template.png")))
    parser.add_argument("--out", dest="out_path", default=str(os.path.join("templates", "blank_template.png")))
    parser.add_argument("--model", default=os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3-pro-image-preview"))
    parser.add_argument("--image-size", default=os.environ.get("GEMINI_IMAGE_SIZE", "2K"))
    parser.add_argument("--max-attempts", type=int, default=int(os.environ.get("GEMINI_MAX_ATTEMPTS", "6")))
    parser.add_argument("--retry-base-delay-s", type=float, default=float(os.environ.get("GEMINI_RETRY_BASE_DELAY_S", "2")))
    parser.add_argument("--timeout-s", type=float, default=float(os.environ.get("GEMINI_HTTP_TIMEOUT_S", "180")))
    parser.add_argument(
        "--prompt",
        default=(
            "The image is a trading card template. You are cleaning up formatting artifacts. "
            "Output the exact same image, but with the following corrections: "
            "1. Remove the square brackets '[ ]' around the Rarity text in the top right (e.g. '[RARITY]'). Keep the text 'RARITY' (or whatever text is inside) but delete the brackets. "
            "2. Ensure NO other brackets exist in the image. "
            "CRITICAL: "
            "- Do NOT remove the Rarity icon (the diamond/shape next to the text). "
            "- Do NOT change the card frame or other text. "
            "- The goal is just to delete the square brackets around the Rarity label."
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
