"""REQ-PPAUG-035 regressions for full-card Gemini reference packs."""
from __future__ import annotations

import hashlib
import io
import json
import types as namespace
from pathlib import Path

import pytest
from PIL import Image

from hypertext.cards import template_matrix
from hypertext.gemini import style
from hypertext.gemini.reference_pack import (
    FINISHED_REFERENCE_MANIFEST,
    FINISHED_REFERENCE_CONTRACT,
    ReferenceContractError,
    ReferencePack,
    build_reference_pack,
)
from hypertext.gemini.style import reference_role_labels
from hypertext.pipeline import daily


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: str | bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, bytes):
        path.write_bytes(value)
    else:
        path.write_text(value, encoding="utf-8")
    return path


def _template_record(root: Path, card_type: str = "NOUN", rarity: str = "COMMON") -> dict:
    image = _write(
        root / "templates/card/v777/composed/noun/common/template_1024x1536.png",
        b"corrected-template",
    )
    manifest = _write(root / "template-manifest.json", '{"fixture":true}\n')
    return {
        "type": card_type,
        "rarity": rarity,
        "path": image,
        "sha256": _sha(image),
        "manifest_path": manifest,
        "manifest_sha256": _sha(manifest),
        "template_version": "v777",
        "template_commit": "fixture-commit",
        "manifest_status": "operator-accepted-canonical",
    }


def _recipe(word: str, art: str, *, card_type: str = "NOUN", rarity: str = "COMMON",
            stats: tuple[int, int, int] = (3, 3, 3)) -> dict:
    return {"content": {
        "WORD": word,
        "GLOSS": f"meaning of {word.lower()}",
        "ABILITY_TEXT": f"Use {word.lower()} with wisdom.",
        "ART_PROMPT": art,
        "CARD_TYPE": card_type,
        "RARITY_TEXT": rarity,
        "STAT_LORE": stats[0],
        "STAT_CONTEXT": stats[1],
        "STAT_COMPLEXITY": stats[2],
        "TRIVIA_BULLETS": [f"{word} trivia"],
    }}


def _candidate(
    root: Path,
    candidate_id: str,
    *,
    word: str,
    art: str,
    prompt: str,
    card_type: str = "NOUN",
    rarity: str = "COMMON",
    status: str = "accepted",
    finished: bool = True,
    legacy: bool = False,
    superseded_by: str | None = None,
    wrong_sha: bool = False,
    stats: tuple[int, int, int] = (3, 3, 3),
) -> dict:
    directory = root / "finished" / candidate_id
    image = _write(directory / "outputs/card_1024x1536.png", candidate_id.encode())
    recipe = _recipe(word, art, card_type=card_type, rarity=rarity, stats=stats)
    recipe_path = _write(directory / "card.json", json.dumps(recipe))
    prompt_path = _write(directory / "prompt.txt", prompt)
    metadata_path = _write(
        directory / "meta.yml",
        f"card_type: {card_type}\nrarity: {rarity}\nreview_status: green\nreview_score: 100\n",
    )
    evidence = {
        "passed": True,
        "score": 100,
        "card_type": card_type,
        "rarity": rarity,
    }
    evidence_path = _write(directory / "grade.json", json.dumps(evidence))
    return {
        "id": candidate_id,
        "status": status,
        "finished": finished,
        "legacy": legacy,
        "superseded_by": superseded_by,
        "card_type": card_type,
        "rarity": rarity,
        "path": str(image),
        "sha256": "0" * 64 if wrong_sha else _sha(image),
        "recipe_path": str(recipe_path),
        "prompt_path": str(prompt_path),
        "metadata_path": str(metadata_path),
        "review": {"status": "green", "score": 100, "evidence_path": str(evidence_path)},
    }


def _manifest(root: Path, entries: list[dict]) -> Path:
    return _write(root / "finished-card-references.json", json.dumps({
        "contract": FINISHED_REFERENCE_CONTRACT,
        "status": "curated",
        "entries": entries,
    }))


def _live_manifest_with_moses_accepted(tmp_path: Path) -> Path:
    """The live manifest retired the MOSES example (pre-matrix style); these
    contract tests need an accepted NAME/COMMON example, so re-accept it in a
    temporary copy rather than depending on curation state."""
    live = json.loads(FINISHED_REFERENCE_MANIFEST.read_text(encoding="utf-8"))
    for entry in live["entries"]:
        if entry["id"] == "013-moses":
            entry["status"] = "accepted"
            entry["legacy"] = False
    return _write(tmp_path / "live-manifest-moses-accepted.json", json.dumps(live))


def test_daily_regression_template_is_not_appended_after_examples(tmp_path):
    """Reproduces the old seam: daily appended TEMPLATE last while style labeled [1]."""
    recipe = _recipe("MOSES", "basket reeds river", card_type="NAME")
    pack = daily._build_style_refs(
        Path("series/2026-Q1"),
        target_type="NAME",
        target_rarity="COMMON",
        target_recipe=recipe,
        target_prompt="basket reeds river",
        reference_manifest_path=_live_manifest_with_moses_accepted(tmp_path),
    )
    assert [item.role for item in pack.references] == ["template", "example"]
    assert pack.references[0].gemini_label.startswith("[1] = TEMPLATE:")
    assert "013-moses" in pack.references[1].path
    # This is the exact defective ordering that must never recur.
    assert [pack.references[1].path, pack.references[0].path] != [
        item.path for item in pack.references
    ]


def test_generate_and_fix_positions_share_gemini_role_contract(tmp_path):
    manifest = _live_manifest_with_moses_accepted(tmp_path)
    generate = daily._build_style_refs(
        tmp_path, target_type="NAME", target_rarity="COMMON",
        target_recipe=_recipe("MOSES", "basket river", card_type="NAME"),
        target_prompt="basket river",
        reference_manifest_path=manifest,
    )
    current = _write(tmp_path / "current-card.png", b"current-card")
    fix = daily._build_style_refs(
        tmp_path,
        current_card_path=current,
        target_type="NAME",
        target_rarity="COMMON",
        target_recipe=_recipe("MOSES", "basket river", card_type="NAME"),
        target_prompt="basket river",
        fix_mode=True,
        reference_manifest_path=manifest,
    )

    assert [item.role for item in generate.references] == ["template", "example"]
    assert [item.role for item in fix.references] == ["current_card", "template", "example"]
    assert reference_role_labels(generate)[0].startswith("[1] = TEMPLATE:")
    assert reference_role_labels(fix)[1].startswith("[2] = TEMPLATE:")
    assert generate.rarity_labels == {1: "COMMON", 2: "COMMON"}
    assert fix.rarity_labels == {1: "COMMON", 2: "COMMON", 3: "COMMON"}
    assert Path(fix.paths[0]) != current
    current.write_bytes(b"replacement-output")
    fix.validate()  # hashes the preserved input snapshot, not the overwritten output


def test_type_by_rarity_manifest_record_is_the_structural_reference():
    record = template_matrix.resolve_template_record("VERB", "GLORIOUS")
    pack = daily._build_style_refs(
        Path("series/2026-Q1"), target_type="VERB", target_rarity="GLORIOUS"
    )
    assert pack.template.path == record["repo_path"]
    assert pack.template.sha256 == record["sha256"]
    assert pack.template.template_version == "v001"
    assert pack.template.template_commit == record["template_commit"]
    assert pack.template.source_manifest.endswith("templates/card/v001/composed/manifest.json")


def test_top_x_similarity_beats_lexicographic_first(tmp_path, monkeypatch):
    target = _recipe("COVENANT", "golden covenant hands stone altar", stats=(5, 4, 3))
    low = _candidate(
        tmp_path, "000-lexicographic-first", word="OCEAN", art="blue fish waves",
        prompt="unrelated ocean fish", stats=(0, 0, 0),
    )
    medium = _candidate(
        tmp_path, "500-medium", word="PROMISE", art="golden hands altar",
        prompt="golden hands solemn promise", stats=(5, 3, 3),
    )
    high = _candidate(
        tmp_path, "999-best", word="COVENANT", art="golden covenant hands stone altar",
        prompt="golden covenant hands stone altar", stats=(5, 4, 3),
    )
    manifest = _manifest(tmp_path, [low, medium, high])
    record = _template_record(tmp_path)

    monkeypatch.setattr(daily, "resolve_template_record", lambda *_args, **_kwargs: record)
    pack = daily._build_style_refs(
        tmp_path,
        target_type="NOUN", target_rarity="COMMON",
        target_recipe=target,
        target_prompt="golden covenant hands stone altar",
        max_examples=2,
        reference_manifest_path=manifest,
    )

    assert [Path(item.path).parts[-3] for item in pack.examples] == ["999-best", "500-medium"]
    assert pack.examples[0].similarity_score > pack.examples[1].similarity_score
    audit = {item["id"]: item for item in pack.candidate_audit}
    assert audit["000-lexicographic-first"]["eligible"] is True
    assert audit["000-lexicographic-first"]["selected"] is False
    assert "tie_break=sha256,path" in pack.examples[0].similarity_reason


def test_ineligible_assets_are_audited_and_never_selected(tmp_path):
    entries = [
        _candidate(tmp_path, "good", word="GOOD", art="gold light", prompt="gold light"),
        _candidate(tmp_path, "legacy-see-face", word="SEE", art="eye", prompt="eye", legacy=True),
        _candidate(tmp_path, "rejected", word="BAD", art="bad", prompt="bad", status="rejected"),
        _candidate(tmp_path, "superseded", word="OLD", art="old", prompt="old", superseded_by="new"),
        _candidate(tmp_path, "unverified", word="HASH", art="hash", prompt="hash", wrong_sha=True),
        _candidate(tmp_path, "wrong-type", word="RUN", art="run", prompt="run", card_type="VERB"),
        _candidate(tmp_path, "wrong-rarity", word="RARE", art="rare", prompt="rare", rarity="RARE"),
    ]
    pack = build_reference_pack(
        template_record=_template_record(tmp_path),
        target_type="NOUN",
        target_rarity="COMMON",
        target_recipe=_recipe("GOOD", "gold light"),
        target_prompt="gold light",
        manifest_path=_manifest(tmp_path, entries),
        root=tmp_path,
    )
    assert [Path(item.path).parts[-3] for item in pack.examples] == ["good"]
    audit = {item["id"]: item for item in pack.candidate_audit}
    assert "legacy!=false" in audit["legacy-see-face"]["eligibility_reasons"]
    assert "status=rejected" in audit["rejected"]["eligibility_reasons"]
    assert any(reason.startswith("superseded_by=") for reason in audit["superseded"]["eligibility_reasons"])
    assert "image_sha256_mismatch" in audit["unverified"]["eligibility_reasons"]
    assert any("target_type_mismatch" in reason for reason in audit["wrong-type"]["eligibility_reasons"])
    assert any("target_rarity_mismatch" in reason for reason in audit["wrong-rarity"]["eligibility_reasons"])


def test_missing_or_legacy_template_never_falls_back_to_base(tmp_path):
    base = _write(tmp_path / "templates/card/v001/base/template_1024x1536.png", b"old-base")
    manifest = _write(tmp_path / "manifest.json", json.dumps({
        "schema_version": 1,
        "status": "operator-accepted-canonical",
        "outputs": [{
            "type": "NOUN", "rarity": "COMMON",
            "visible_type_label": "NOUN", "visible_rarity_label": "COMMON",
            "path": str(base.relative_to(tmp_path)), "sha256": _sha(base),
        }],
    }))
    with pytest.raises(ValueError, match="forbidden fallback"):
        template_matrix.resolve_template_record(
            "NOUN", "COMMON", manifest_path=manifest, root=tmp_path
        )

    corrupted = _template_record(tmp_path)
    corrupted["sha256"] = "0" * 64
    with pytest.raises(ReferenceContractError, match="failed SHA-256"):
        build_reference_pack(
            template_record=corrupted,
            target_type="NOUN",
            target_rarity="COMMON",
            manifest_path=_manifest(tmp_path, []),
            root=tmp_path,
        )


def test_pack_rejects_independent_role_or_rarity_drift():
    pack = daily._build_style_refs(
        Path("series/2026-Q1"), target_type="VERB", target_rarity="GLORIOUS"
    )
    payload = pack.to_dict()
    payload["references"][0]["gemini_label"] = "[1] = EXAMPLE"
    with pytest.raises(ReferenceContractError, match="role label drift"):
        ReferencePack.from_dict(payload)


def test_gemini_contents_use_the_contract_template_label(monkeypatch, tmp_path):
    pack = daily._build_style_refs(
        tmp_path, target_type="VERB", target_rarity="GLORIOUS"
    )
    generated = io.BytesIO()
    Image.new("RGB", (1024, 1536), "navy").save(generated, format="PNG")
    inline = namespace.SimpleNamespace(mime_type="image/png", data=generated.getvalue())
    response = namespace.SimpleNamespace(candidates=[namespace.SimpleNamespace(
        content=namespace.SimpleNamespace(parts=[namespace.SimpleNamespace(inline_data=inline)]),
    )])
    calls = []
    client = namespace.SimpleNamespace(models=namespace.SimpleNamespace(
        generate_content=lambda **kwargs: calls.append(kwargs) or response
    ))

    class FakePart:
        @staticmethod
        def from_bytes(data, mime_type):
            return namespace.SimpleNamespace(data=data, mime_type=mime_type)

        @staticmethod
        def from_text(text):
            return namespace.SimpleNamespace(text=text)

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(style, "genai", namespace.SimpleNamespace(Client=lambda api_key: client))
    monkeypatch.setattr(style, "types", namespace.SimpleNamespace(
        Part=FakePart,
        GenerateContentConfig=lambda **kwargs: kwargs,
        ImageConfig=lambda **kwargs: kwargs,
    ))
    out = tmp_path / "generated.png"
    style.generate_with_styles(
        "serialized recipe", pack.paths, str(out), reference_pack=pack
    )

    contents = calls[0]["contents"]
    assert contents[0].text.startswith("IMAGE [1] = TEMPLATE:")
    assert "STRUCTURE (copy EXACTLY from [1] - the template)" in contents[-1].text


def test_machine_provenance_records_complete_reference_request_and_output(tmp_path):
    card_dir = tmp_path / "card"
    outputs = card_dir / "outputs"
    recipe = _recipe("MOSES", "basket river", card_type="NAME")
    prompt = "serialized full-card recipe prompt"
    _write(card_dir / "card.json", json.dumps(recipe))
    prompt_path = _write(card_dir / "prompt.txt", prompt)
    output = _write(outputs / "card_1024x1536.png", b"final-full-card-output")
    pack = daily._build_style_refs(
        tmp_path,
        target_type="NAME",
        target_rarity="COMMON",
        target_recipe=recipe,
        target_prompt=prompt,
    )
    pack.write(outputs / "reference-pack.json")
    _write(outputs / "generation.json", json.dumps({
        "model": "gemini-test", "output_sha256": "a" * 64,
    }))

    daily._write_generation_log(
        card_dir, reference_pack=pack, prompt_file=prompt_path, phase="test"
    )
    provenance = json.loads((outputs / "generation-provenance.json").read_text())

    assert provenance["settings"]["full_card_generation"] is True
    assert provenance["settings"]["model"] == "gemini-test"
    assert provenance["recipe"]["canonical_sha256"]
    assert provenance["prompt"]["sha256"] == hashlib.sha256(prompt.encode()).hexdigest()
    assert provenance["output"]["sha256"] == _sha(output)
    assert provenance["output"]["gemini_output_sha256"] == "a" * 64
    for item in provenance["reference_pack"]["references"]:
        assert item["path"] and item["resolved_path"] and item["sha256"]
        assert item["eligible"] is True and item["eligibility_reasons"]
        assert item["assigned_role"] == item["role"]
        assert item["role"] and item["gemini_label"] and item["rarity_label"] == "COMMON"
        assert "similarity_reason" in item and "similarity_score" in item
    template = provenance["reference_pack"]["references"][0]
    assert template["role"] == "template"
    assert template["template_version"] == "v001"
    assert template["template_commit"]
