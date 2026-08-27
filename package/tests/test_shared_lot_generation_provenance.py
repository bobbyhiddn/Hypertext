import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.skipif(
    not (ROOT / "templates/archive").exists(),
    reason="cold evidence archive not present - run scripts/fetch_evidence.sh")

ARCHIVES = (ROOT / "templates/archive/pre-v002-lot-rework",
            ROOT / "templates/archive/matrix-provenance")

def resolve(relative):
    """Recorded paths predate the 2026-08 archive moves; fall back to the archives."""
    path = ROOT / relative
    if path.exists():
        return path
    for archive in ARCHIVES:
        candidate = archive / relative
        if candidate.exists():
            return candidate
    return path



def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_shared_lots_are_complete_model_outputs_with_traceable_references():
    manifest = json.loads((resolve("templates/lot/v001/shared/manifest.json")).read_text())
    assert manifest["requirements"] == ["REQ-PPAUG-017", "REQ-PPAUG-020", "REQ-PPAUG-025", "REQ-PPAUG-026", "REQ-PPAUG-027"]
    assert manifest["model"] == "gemini-3.1-flash-image"
    assert "complete-face" in manifest["generation_policy"]
    assert manifest["prohibited_operations"] == [
        "text overlay on faces", "face compositing", "programmatic face construction"
    ]
    assert len(manifest["references"]) == 3
    for reference in manifest["references"]:
        assert digest(resolve(reference["path"])) == reference["sha256"]

    expected = {
        5: ("REMNANT", "5 SAME TYPE", "8 POINTS", "2 LETTERS"),
        6: ("CONGREGATION", "6 ANY MIX", "10 POINTS", "2 LETTERS"),
        7: ("CREATION", "3 + 2 + 2 (THREE TYPES)", "14 POINTS", "3 LETTERS"),
    }
    assert len(manifest["cells"]) == 3
    for cell in manifest["cells"]:
        assert (cell["title"], cell["recipe"], cell["chapter_value"], cell["page_value"]) == expected[cell["cards"]]
        output = resolve(cell["path"])
        assert digest(output) == cell["sha256"]
        assert digest(resolve(cell["generation_record"])) == cell["generation_record_sha256"]
        with Image.open(output) as image:
            assert image.format == "PNG"
            assert image.mode == "RGB"
            assert image.size == (1024, 1536)
        assert "entirely new, complete" in cell["prompt"]
        assert "do not edit, paint onto, trace, paste, composite" in cell["prompt"]
        assert "do not create separate role treatments" in cell["prompt"]


def test_review_matrix_and_mirrored_manifest_are_current():
    review = json.loads(resolve("operator_review/lot-template-family-d2429168/manifest.json").read_text())
    shared = json.loads((resolve("templates/lot/v001/shared/manifest.json")).read_text())
    assert review == shared
    matrix = resolve(review["matrix"])
    assert digest(matrix) == review["matrix_sha256"]
    with Image.open(matrix) as image:
        assert image.format == "PNG"
        assert image.size == (2100, 1080)
