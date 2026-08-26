import copy
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERIFIER_PATH = ROOT / "tools" / "verify_template_package.py"
SPEC = importlib.util.spec_from_file_location(
    "hypertext_template_package_verifier", VERIFIER_PATH
)
assert SPEC and SPEC.loader
verifier = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verifier
SPEC.loader.exec_module(verifier)


def _manifest():
    return json.loads((ROOT / verifier.MANIFEST_REL).read_text(encoding="utf-8"))


def _mutated_errors(tmp_path, mutate):
    manifest = copy.deepcopy(_manifest())
    mutate(manifest)
    path = tmp_path / "persistence-manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return verifier.verify_package(ROOT, path)


def test_exact_persisted_template_package_passes():
    assert verifier.verify_package(ROOT) == []


def test_missing_pair_fails(tmp_path):
    errors = _mutated_errors(
        tmp_path,
        lambda manifest: manifest["templates"].pop(),
    )
    assert any("missing pair" in error for error in errors)


def test_digest_drift_fails(tmp_path):
    def mutate(manifest):
        manifest["templates"][0]["sha256"] = "0" * 64

    errors = _mutated_errors(tmp_path, mutate)
    assert any("digest drift" in error for error in errors)


def test_duplicate_mapping_fails(tmp_path):
    def mutate(manifest):
        manifest["templates"].append(copy.deepcopy(manifest["templates"][0]))

    errors = _mutated_errors(tmp_path, mutate)
    assert any("duplicate mapping" in error for error in errors)


def test_legacy_fallback_fails(tmp_path):
    def mutate(manifest):
        manifest["templates"][0]["path"] = (
            "templates/card/v001/noun/template_1024x1536.png"
        )

    errors = _mutated_errors(tmp_path, mutate)
    assert any("legacy fallback" in error for error in errors)


def test_finished_card_substitution_fails(tmp_path):
    def mutate(manifest):
        manifest["templates"][0]["path"] = (
            "series/2026-Q1/cards/001-grace/outputs/card_1024x1536.png"
        )

    errors = _mutated_errors(tmp_path, mutate)
    assert any("finished-card substitution" in error for error in errors)
