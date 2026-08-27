import pytest

from hypertext.quality import (
    QUALITY_GATE, QualityContractError, assemble_art_prompt, deterministic_repairs,
    provenance, quality_score, select_candidate, select_references, validate_plan,
)


def card():
    return {"content": {"NUMBER": "007", "WORD": "LIGHT", "CARD_TYPE": "NOUN",
            "RARITY_TEXT": "COMMON", "ART_PROMPT": "a lamp in a dark room",
            "STAT_LORE": 3, "STAT_CONTEXT": 2, "STAT_COMPLEXITY": 1}}


def test_plan_and_art_prompt_exclude_model_text():
    validate_plan(card())
    prompt = assemble_art_prompt(card())
    assert "No words, letters, numerals" in prompt
    assert "stat pips" in prompt


def test_plan_rejects_invalid_pips():
    value = card(); value["content"]["STAT_LORE"] = 6
    with pytest.raises(QualityContractError):
        validate_plan(value)


def test_reference_selection_is_stable_and_only_uses_gate_passes():
    refs = [{"path": "b", "card_type": "NOUN", "rarity": "COMMON", "quality_score": 99},
            {"path": "a", "card_type": "NOUN", "rarity": "COMMON", "quality_score": 100}]
    assert [r["path"] for r in select_references(refs, card_type="NOUN", rarity="COMMON")] == ["a"]


def test_candidate_timeout_is_never_success_and_ties_are_deterministic():
    candidates = [{"index": 0, "status": "timeout"},
                  {"index": 2, "status": "success", "image_bytes": b"x", "contract_score": 100},
                  {"index": 1, "status": "success", "image_bytes": b"y", "contract_score": 100}]
    assert select_candidate(candidates)["index"] == 1
    with pytest.raises(QualityContractError):
        select_candidate([{"status": "timeout"}])


def test_all_dimensions_must_reach_100_gate():
    scores = {name: 100 for name in ("composition", "typography", "template_fidelity",
              "metadata", "stat_pips", "artifact_cleanliness")}
    assert quality_score(scores) == {"dimensions": scores, "score": 100, "passed": True, "gate": QUALITY_GATE}
    scores["typography"] = 99
    assert quality_score(scores)["passed"] is False


def test_only_deterministic_repairs_are_allowed_and_provenance_is_bounded():
    assert deterministic_repairs(["format", "stat_pips"]) == ["convert_to_png", "redraw_stat_pips"]
    with pytest.raises(QualityContractError):
        deterministic_repairs(["ask_model_to_fix_text"])
    assert provenance("review", {"a": 1}, {"score": 100}, attempt=4).attempt == 4
    with pytest.raises(QualityContractError):
        provenance("review", {}, {}, attempt=5)
