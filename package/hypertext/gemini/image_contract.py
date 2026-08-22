"""Shared, offline-testable contracts for Gemini image generation."""

from __future__ import annotations

import base64
import io
import json
import os
import tempfile
from pathlib import Path

from PIL import Image

EXPECTED_DIMENSIONS = (1024, 1536)
ALLOWED_MIME_TYPES = {"image/png"}
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 4


class ImageContractError(RuntimeError):
    """A permanent response/output contract failure."""


def validate_request(aspect_ratio: str, image_size: str) -> None:
    if (aspect_ratio, image_size) != ("2:3", "2K"):
        raise ImageContractError("Hypertext images require aspect ratio 2:3 and size 2K")


def decode_and_validate(data: bytes | str, mime_type: str) -> tuple[bytes, tuple[int, int]]:
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ImageContractError(f"Unsupported image MIME type: {mime_type or 'missing'}")
    if isinstance(data, str):
        try:
            data = base64.b64decode(data, validate=True)
        except (ValueError, TypeError, base64.binascii.Error) as exc:
            raise ImageContractError("Gemini returned malformed base64 image data") from exc
    if not isinstance(data, bytes):
        raise ImageContractError("Gemini returned non-bytes image data")
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            dimensions = image.size
            image_format = image.format
    except Exception as exc:
        raise ImageContractError("Gemini returned corrupt image bytes") from exc
    if image_format != "PNG":
        raise ImageContractError(f"Image bytes do not match declared MIME type: {image_format}")
    if dimensions != EXPECTED_DIMENSIONS:
        raise ImageContractError(
            f"Wrong image dimensions: {dimensions[0]}x{dimensions[1]}; expected 1024x1536"
        )
    return data, dimensions


def classify_error(exc: Exception) -> tuple[str, int | None, bool]:
    status = getattr(exc, "status_code", getattr(exc, "code", None))
    try:
        status = int(status) if status is not None else None
    except (TypeError, ValueError):
        status = None
    if status in RETRYABLE_STATUS_CODES:
        return "transient_http", status, True
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return "transient_network", status, True
    reason = getattr(exc, "reason", None)
    if isinstance(reason, (TimeoutError, ConnectionError)):
        return "transient_network", status, True
    return "permanent", status, False


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def record_success(out_path: str, *, model: str, mime_type: str,
                   dimensions: tuple[int, int], attempts: int, reference_count: int) -> None:
    _atomic_json(Path(out_path).parent / "generation.json", {
        "status": "success", "model": model, "mime_type": mime_type,
        "width": dimensions[0], "height": dimensions[1], "attempts": attempts,
        "reference_count": reference_count,
    })


def record_failure(out_path: str, *, model: str, category: str,
                   attempts: int, reference_count: int, status_code: int | None = None) -> None:
    payload = {"status": "failure", "category": category, "model": model,
               "attempts": attempts, "reference_count": reference_count}
    if status_code is not None:
        payload["status_code"] = status_code
    _atomic_json(Path(out_path).parent / "generation.json", payload)


def atomic_write_image(out_path: str, data: bytes) -> None:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
