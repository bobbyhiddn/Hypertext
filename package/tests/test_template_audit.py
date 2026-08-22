import json
from pathlib import Path
from unittest import mock

from hypertext.pipeline import template_audit


def test_completed_manifest_has_no_unresolved_flags():
    manifest = template_audit.load_manifest()
    assert manifest["status"] == "completed-accepted"
    assert manifest["templates"] == []
    assert template_audit.audit() == []


def test_completed_lot_manifest_has_no_legacy_visible_label_flags():
    assert template_audit.audit("lot") == []


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
