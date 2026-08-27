"""Offline contract checks and durable regeneration flags for curated templates."""
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "templates" / "regeneration_manifest.json"
EXPECTED_SIZE = (1024, 1536)

def load_manifest(path: Path = MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def asset_contract_failures(relative_path: str) -> list[str]:
    path = ROOT / relative_path
    if not path.is_file(): return ["missing_asset"]
    try:
        with Image.open(path) as image:
            image.load(); size, fmt = image.size, image.format
    except Exception: return ["invalid_image"]
    failures = []
    if size != EXPECTED_SIZE: failures.append(f"dimensions:{size[0]}x{size[1]}")
    if fmt != "PNG": failures.append(f"mime_extension:image/{(fmt or 'unknown').lower()}:.png")
    return failures

def definition_contract_failures(entry: dict) -> list[str]:
    failures = []
    if entry.get("prompt"):
        text = (ROOT / entry["prompt"]).read_text(encoding="utf-8")
        if entry["family"] == "lot" and "[NOUN]" in text: failures.append("composition_labels_bracketed")
        if entry["subtype"] == "base" and "X-CARDS" in text: failures.append("card_count_label_plural")
    return failures

def current_failures(entry: dict) -> list[str]:
    return asset_contract_failures(entry["asset"]) + definition_contract_failures(entry)

def audit(template_type: str | None = None) -> list[tuple[dict, list[str]]]:
    entries = load_manifest()["templates"]
    if template_type: entries = [e for e in entries if e["family"] == template_type]
    return [(entry, current_failures(entry)) for entry in entries]

def clear_resolved_flag(template_type: str, subtype: str, path: Path = MANIFEST) -> bool:
    """Clear only when the corrected asset and definition pass every contract."""
    data = load_manifest(path); before = len(data["templates"])
    data["templates"] = [e for e in data["templates"] if not (
        e["family"] == template_type and e["subtype"] == subtype and not current_failures(e))]
    changed = len(data["templates"]) != before
    if changed: path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return changed
