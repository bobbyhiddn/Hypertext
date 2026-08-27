#!/usr/bin/env python3
"""Gemini text generation with optional Google Search grounding.

This module provides a pure urllib-based implementation for Gemini text
generation, with retry logic and grounding metadata extraction.
"""

import json
import os
import random
import sys
import time
import urllib.error
import urllib.request

from hypertext.gemini.config import text_model


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


def generate_text(
    prompt: str,
    *,
    model: str | None = None,
    temperature: float | None = None,
    use_google_search: bool = False,
) -> str:
    """Generate text from a prompt using Gemini.

    Args:
        prompt: The text prompt to send to Gemini.
        model: Optional model ID override.
        temperature: Optional temperature setting.
        use_google_search: Whether to enable Google Search grounding.

    Returns:
        The generated text response.
    """
    text, _grounding = generate_text_with_grounding(
        prompt,
        model=model,
        temperature=temperature,
        use_google_search=use_google_search,
    )
    return text


def _driver_exchange(prompt: str, *, temperature, use_google_search: bool) -> str:
    """Operator-driven text mode (HYPERTEXT_TEXT_DRIVER_DIR).

    Spools the prompt to a numbered file and blocks until the operator (or an
    operator-controlled agent) writes the matching response file. Everything
    downstream - validators, independent critic, assembly, provenance - runs
    unchanged; only the author of the text differs. Exchanges stay on disk as
    part of the planning record.
    """
    from pathlib import Path

    root = Path(os.environ["HYPERTEXT_TEXT_DRIVER_DIR"])
    root.mkdir(parents=True, exist_ok=True)
    seq_file = root / "seq"
    seq = int(seq_file.read_text()) + 1 if seq_file.exists() else 1
    seq_file.write_text(str(seq))
    stem = f"{seq:04d}"
    (root / f"{stem}-meta.json").write_text(json.dumps(
        {"temperature": temperature, "use_google_search": bool(use_google_search)}))
    prompt_path = root / f"{stem}-prompt.txt"
    tmp_path = root / f"{stem}-prompt.tmp"
    tmp_path.write_text(prompt)
    tmp_path.rename(prompt_path)
    response = root / f"{stem}-response.txt"
    deadline = time.time() + float(os.environ.get("HYPERTEXT_TEXT_DRIVER_TIMEOUT_S", "3600"))
    while time.time() < deadline:
        if response.exists():
            text = response.read_text()
            if text.strip():
                return text
        time.sleep(0.5)
    raise RuntimeError(f"text driver timed out waiting for {response}")


def generate_text_with_grounding(
    prompt: str,
    *,
    model: str | None = None,
    temperature: float | None = None,
    use_google_search: bool = False,
) -> tuple[str, dict]:
    """Generate text with grounding metadata.

    Args:
        prompt: The text prompt to send to Gemini.
        model: Optional model ID override.
        temperature: Optional temperature setting.
        use_google_search: Whether to enable Google Search grounding.

    Returns:
        Tuple of (generated_text, grounding_metadata).
        Grounding metadata includes 'queries' and 'sources' lists.
    """
    if os.environ.get("HYPERTEXT_TEXT_DRIVER_DIR"):
        driven = _driver_exchange(prompt, temperature=temperature, use_google_search=use_google_search)
        return driven, {"queries": [], "sources": []}
    api_key = os.environ.get("GEMINI_TEXT_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_TEXT_API_KEY (or GEMINI_API_KEY) env var is not set.")

    model_id = model or text_model()
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"

    payload: dict = {
        "contents": [{"parts": [{"text": prompt}]}],
    }

    if temperature is not None:
        payload["generationConfig"] = {"temperature": temperature}

    if use_google_search:
        payload["tools"] = [{"google_search": {}}]

    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    max_attempts = int(os.environ.get("GEMINI_TEXT_MAX_ATTEMPTS", "6"))
    base_delay_s = float(os.environ.get("GEMINI_TEXT_RETRY_BASE_DELAY_S", "2"))
    timeout_s = float(os.environ.get("GEMINI_TEXT_HTTP_TIMEOUT_S", "240"))

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
        except TimeoutError as e:
            if attempt < max_attempts:
                delay = base_delay_s * (2 ** (attempt - 1)) + random.random()
                print(
                    f"Gemini text request timed out. Retrying in {delay:.1f}s (attempt {attempt}/{max_attempts}).",
                    file=sys.stderr,
                )
                time.sleep(delay)
                last_error = e
                continue
            raise
        except urllib.error.HTTPError as e:
            body = _read_http_error_body(e)
            retry_after = _parse_retry_after_seconds(getattr(e, "headers", None))
            retriable = e.code in (429, 500, 502, 503, 504)

            if retriable and attempt < max_attempts:
                delay = retry_after if retry_after is not None else (base_delay_s * (2 ** (attempt - 1)))
                delay = delay + random.random()
                print(
                    f"Gemini text request failed with HTTP {e.code}. Retrying in {delay:.1f}s (attempt {attempt}/{max_attempts}).",
                    file=sys.stderr,
                )
                if body:
                    print(f"Gemini error body (truncated): {body[:800]}", file=sys.stderr)
                time.sleep(delay)
                last_error = e
                continue

            msg = f"Gemini text request failed with HTTP {e.code}: {e.reason}"
            if body:
                msg += f"\nBody (truncated): {body[:2000]}"
            raise RuntimeError(msg) from e
        except urllib.error.URLError as e:
            if attempt < max_attempts:
                delay = base_delay_s * (2 ** (attempt - 1)) + random.random()
                print(
                    f"Gemini text request failed with URLError: {e}. Retrying in {delay:.1f}s (attempt {attempt}/{max_attempts}).",
                    file=sys.stderr,
                )
                time.sleep(delay)
                last_error = e
                continue
            raise

    if last_error is not None or data is None:
        raise RuntimeError("Gemini text request failed after retries.") from last_error

    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"No candidates returned. Raw: {raw[:500]}")

    first = candidates[0]
    finish_reason = first.get("finishReason", "")

    # Check for malformed function call - this is a retriable API error
    if finish_reason == "MALFORMED_FUNCTION_CALL":
        # Retry the request without grounding as a fallback
        print(
            "Gemini returned MALFORMED_FUNCTION_CALL. Retrying without grounding...",
            file=sys.stderr,
        )
        # Fall back to non-grounded request
        payload_no_ground = {
            "contents": [{"parts": [{"text": prompt}]}],
        }
        if temperature is not None:
            payload_no_ground["generationConfig"] = {"temperature": temperature}
        body_no_ground = json.dumps(payload_no_ground).encode("utf-8")
        req_no_ground = urllib.request.Request(endpoint, data=body_no_ground, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req_no_ground, timeout=timeout_s) as resp:
                raw = resp.read().decode("utf-8")
                data = json.loads(raw)
            candidates = data.get("candidates", [])
            if candidates:
                first = candidates[0]
        except Exception as e:
            raise RuntimeError(f"Fallback request without grounding also failed: {e}") from e

    parts = first.get("content", {}).get("parts", [])
    texts: list[str] = []
    for p in parts:
        t = p.get("text")
        if t:
            texts.append(t)

    if not texts:
        raise RuntimeError(f"No text parts found. Raw: {raw[:800]}")

    grounding_meta = first.get("groundingMetadata", {}) if isinstance(first.get("groundingMetadata"), dict) else {}
    queries = grounding_meta.get("webSearchQueries", [])
    if not isinstance(queries, list):
        queries = []

    sources: list[dict] = []
    seen_uris: set[str] = set()
    chunks = grounding_meta.get("groundingChunks", [])
    if isinstance(chunks, list):
        for c in chunks:
            if not isinstance(c, dict):
                continue
            web = c.get("web")
            if not isinstance(web, dict):
                continue
            uri = str(web.get("uri", "")).strip()
            title = str(web.get("title", "")).strip()
            if not uri or uri in seen_uris:
                continue
            seen_uris.add(uri)
            sources.append({"uri": uri, "title": title})

    text_out = "\n".join(texts).strip()
    return text_out, {"queries": queries, "sources": sources}


def main() -> int:
    """CLI entrypoint for testing text generation."""
    if len(sys.argv) < 2:
        print("Usage: python -m hypertext.gemini.text <prompt_file>")
        return 1

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        prompt = f.read().strip()

    print(generate_text(prompt, use_google_search=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
