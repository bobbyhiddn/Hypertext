#!/usr/bin/env python3
"""Verify every face region in the REQ-PPAUG-024 collage against its source blob."""
import hashlib
import io
import json
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "operator_review/constructed/e50961ad0f4d"
PROVENANCE = OUT / "visual_acceptance_review_5x4.provenance.json"
COLLAGE = OUT / "visual_acceptance_review_5x4.png"

def main() -> None:
    manifest = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    assert hashlib.sha256(COLLAGE.read_bytes()).hexdigest() == manifest["collage_byte_sha256"]
    collage = Image.open(COLLAGE).convert("RGB")
    seen = set()
    for cell in manifest["cells"]:
        path = cell["repository_path"]
        assert path not in seen
        seen.add(path)
        raw = subprocess.run(["git", "-C", str(ROOT), "show",
                              f'{cell["authority_commit"]}:{path}'], check=True,
                             capture_output=True).stdout
        assert hashlib.sha256(raw).hexdigest() == cell["source_byte_sha256"]
        blob = subprocess.run(["git", "-C", str(ROOT), "rev-parse",
                               f'{cell["authority_commit"]}:{path}'], check=True,
                              capture_output=True, text=True).stdout.strip()
        assert blob == cell["git_blob_sha"]
        source = Image.open(io.BytesIO(raw)).convert("RGB")
        assert list(source.size) == cell["source_dimensions"]
        rendered = source.resize(tuple(cell["transform"]["rendered_dimensions"]), Image.Resampling.LANCZOS)
        assert hashlib.sha256(rendered.tobytes()).hexdigest() == cell["rendered_rgb_sha256"]
        x, y, w, h = cell["collage_face_bbox_xywh"]
        assert collage.crop((x, y, x+w, y+h)).tobytes() == rendered.tobytes()
    assert len(seen) == 31
    assert manifest["scope"]["native_template_cells"] == 11
    assert manifest["scope"]["completed_sample_cells"] == 20
    print("PASS: 31/31 face regions exactly reconstruct from listed existing Git blobs")

if __name__ == "__main__":
    main()
