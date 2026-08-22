import json
from pathlib import Path
from unittest import mock

from hypertext.pipeline import template_audit


def test_manifest_covers_every_curated_template_and_reproduces_flags():
    expected = {
        *(f"card/{name}" for name in ("base", "common", "uncommon", "rare", "glorious", "noun", "verb", "adjective", "name", "title")),
        *(f"lot/{name}" for name in ("base", "5-card", "6-card", "7-card")),
    }
    results = template_audit.audit()
    assert {f"{entry['family']}/{entry['subtype']}" for entry, _ in results} == expected
    assert all(failures for _, failures in results)
    assert sum("mime_extension" in failure for _, failures in results for failure in failures) == 10
    assert sum("dimensions:848x1264" in failures for _, failures in results) == 14


def test_lot_definition_contract_detects_all_legacy_visible_labels():
    results = template_audit.audit("lot")
    assert len(results) == 4
    assert all("composition_labels_bracketed" in failures for _, failures in results)
    base = next(failures for entry, failures in results if entry["subtype"] == "base")
    assert "card_count_label_plural" in base


def test_stale_flag_clears_only_after_corrected_asset_passes(tmp_path):
    manifest = tmp_path / "manifest.json"
    entry = {"family": "card", "subtype": "base", "asset": "x"}
    manifest.write_text(json.dumps({"templates": [entry]}), encoding="utf-8")
    with mock.patch.object(template_audit, "current_failures", return_value=["dimensions"]):
        assert not template_audit.clear_resolved_flag("card", "base", manifest)
        assert json.loads(manifest.read_text())["templates"] == [entry]
    with mock.patch.object(template_audit, "current_failures", return_value=[]):
        assert template_audit.clear_resolved_flag("card", "base", manifest)
        assert json.loads(manifest.read_text())["templates"] == []
