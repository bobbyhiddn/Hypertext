"""Typed-recipe evaluator, feasibility regression, and manifest agreement."""
import json
from pathlib import Path

import pytest

from hypertext.lots.patterns import opening_hand_probability, satisfies
from hypertext.lots.rules import CHAPTER_VALUE, OWNER_LETTERS, VISITOR_LETTERS, load_lot_rules

ROOT = Path(__file__).resolve().parents[2]
PHASES = {p["id"]: p for p in load_lot_rules()}
MANIFEST = json.loads((ROOT / "series/2026-Q1/lots/manifest.json").read_text())


def test_series_manifest_agrees_with_canonical_recipes():
    assert MANIFEST["count"] == 30
    for lot in MANIFEST["lots"]:
        phase = PHASES[lot["id"]]
        assert lot["name"] == phase["name"] and lot["cards"] == phase["cards"]
        assert lot["chapter_value_points"] == CHAPTER_VALUE[phase["cards"]]
        assert lot["portion_owner_letters"] == OWNER_LETTERS[phase["cards"]]
        assert lot["portion_visitor_letters"] == VISITOR_LETTERS[phase["cards"]]
        assert lot["recipe"]["kind"] == phase["recipe"]["kind"]
        if lot["recipe"]["kind"] == "fixed":
            assert lot["recipe"]["composition"] == phase["recipe"]["composition"]
        elif lot["recipe"]["kind"] == "groups":
            assert ([(g["count"], g["constraint"]) for g in lot["recipe"]["groups"]]
                    == [(g["count"], g["constraint"]) for g in phase["recipe"]["groups"]])


def test_evaluator_gameplay_semantics():
    witness = PHASES[4]["recipe"]  # NAME x2 VERB x2 ADJ
    assert satisfies(witness, {"NAME": 2, "VERB": 2, "ADJECTIVE": 1})
    assert satisfies(witness, {"NAME": 1, "TITLE": 1, "VERB": 2, "ADJECTIVE": 1})  # one TITLE wild
    assert not satisfies(witness, {"TITLE": 2, "VERB": 2, "ADJECTIVE": 1})  # wild capped at one
    remnant = PHASES[1]["recipe"]  # 4 same + 1 any
    assert satisfies(remnant, {"VERB": 4, "NOUN": 1})
    assert satisfies(remnant, {"NOUN": 3, "TITLE": 1, "VERB": 1})  # TITLE completes a NOUN set
    assert not satisfies(remnant, {"VERB": 3, "ADJECTIVE": 3, "NOUN": 1})
    assembly = PHASES[16]["recipe"]  # 3 of one type + 3 of another
    assert satisfies(assembly, {"VERB": 3, "ADJECTIVE": 3})
    assert not satisfies(assembly, {"VERB": 6})  # groups need two distinct types
    creation = PHASES[27]["recipe"]
    assert satisfies(creation, {"NOUN": 3, "VERB": 1, "ADJECTIVE": 1, "NAME": 1, "TITLE": 1})
    # leftovers of two different types are not a pair
    assert not satisfies(creation, {"NOUN": 2, "VERB": 2, "ADJECTIVE": 1, "NAME": 1, "TITLE": 1})
    assert not satisfies(creation, {"NOUN": 1, "VERB": 1, "ADJECTIVE": 1, "NAME": 1, "TITLE": 1})


# 6-card floor admits SANCTUARY (NOUN x4 NAME TITLE, ~1.6%), the tier's deliberate hard end.
BANDS = {5: (0.08, 0.40), 6: (0.012, 0.30), 7: (0.008, 0.15)}


@pytest.mark.parametrize("phase_id", range(1, 31))
def test_opening_hand_feasibility_within_design_band(phase_id):
    phase = PHASES[phase_id]
    p = opening_hand_probability(phase["recipe"])
    lo, hi = BANDS[phase["cards"]]
    assert lo <= p <= hi, f"{phase['name']}: P={p:.4f} outside band {lo}-{hi}"


def test_feasibility_regression_anchors():
    anchors = {2: 0.3767, 4: 0.2101, 16: 0.1434, 27: 0.1323, 30: 0.0210}
    for pid, expected in anchors.items():
        assert opening_hand_probability(PHASES[pid]["recipe"]) == pytest.approx(expected, abs=0.002)
