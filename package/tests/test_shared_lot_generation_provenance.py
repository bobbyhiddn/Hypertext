import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_shared_lots_are_complete_model_outputs_with_traceable_references():
    manifest = json.loads((ROOT / "templates/lot/v001/shared/manifest.json").read_text())
    assert manifest["requirements"] == ["REQ-PPAUG-020", "REQ-PPAUG-025"]
    assert manifest["model"] == "gemini-3.1-flash-image"
    assert "complete-face" in manifest["generation_policy"]
    assert manifest["prohibited_operations"] == [
        "text overlay on faces", "face compositing", "programmatic face construction"
    ]
    assert len(manifest["references"]) == 3
    for reference in manifest["references"]:
        assert digest(ROOT / reference["path"]) == reference["sha256"]

    expected = {
        (5, "chapter"): ("REMNANT", "5 SAME TYPE", "8 POINTS"),
        (5, "page"): ("REMNANT", "5 SAME TYPE", "2 LETTERS"),
        (6, "chapter"): ("CONGREGATION", "6 ANY MIX", "10 POINTS"),
        (6, "page"): ("CONGREGATION", "6 ANY MIX", "2 LETTERS"),
        (7, "chapter"): ("CREATION", "3 + 2 + 2 (THREE TYPES)", "14 POINTS"),
        (7, "page"): ("CREATION", "3 + 2 + 2 (THREE TYPES)", "3 LETTERS"),
    }
    assert len(manifest["cells"]) == 6
    for cell in manifest["cells"]:
        assert (cell["title"], cell["recipe"], cell["reward"]) == expected[(cell["cards"], cell["role"])]
        output = ROOT / cell["path"]
        assert digest(output) == cell["sha256"]
        assert digest(ROOT / cell["generation_record"]) == cell["generation_record_sha256"]
        with Image.open(output) as image:
            assert image.format == "PNG"
            assert image.mode == "RGB"
            assert image.size == (1024, 1536)
        assert "entirely new, complete" in cell["prompt"]
        assert "do not edit, paint onto, trace, paste, composite" in cell["prompt"]


def test_review_matrix_and_mirrored_manifest_are_current():
    review = json.loads((ROOT / "operator_review/lot-template-family-d2429168/manifest.json").read_text())
    shared = json.loads((ROOT / "templates/lot/v001/shared/manifest.json").read_text())
    assert review == shared
    matrix = ROOT / review["matrix"]
    assert digest(matrix) == review["matrix_sha256"]
    with Image.open(matrix) as image:
        assert image.format == "PNG"
        assert image.size == (2100, 2080)
