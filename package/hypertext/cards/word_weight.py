"""Word weight - how much a card of this word means in the set's story.

User (2026-08-28): "word weight needs to be accounted for. a word like
DESTROYER and SODOM need to at least be rare." Rarity had been assigned by the
type-by-rarity grid alone, with a word chosen to fit the cell; the word's own
gravity never entered.

WEIGHT is a 1-5 judgment, separate from LORE (theological weight of the lemma):

  1  everyday vocabulary the era happens to use            HIGH, GATHER, BRICK
  2  descriptive or mechanical words with a clear place    DARK, DEPART, FILLED
  3  thematic vocabulary with real teaching behind it      ELDER, SHEPHERD, FIRE, TONGUE
  4  a named judgment, agent, place, patriarch, or event   SODOM, DESTROYER, EDEN, ABRAM, ARK
     the era turns on - the card people will look for
  5  a pillar of the set: the act or name the whole story   SPIRIT, COVENANT, CREATE, NOAH, ADAM
     hangs on - the chase card

Floors are deterministic: weight 5 must print GLORIOUS, weight 4 at least
RARE; weight 3 and below may print at any rarity. Because RARE and GLORIOUS
together are 22 of 90 slots, a set may carry at most about 22 words of weight 4
or 5, and at most 9 of weight 5 - the audit reports the running count so the
remaining slots are planned with that budget in mind.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

RARITY_ORDER = ("COMMON", "UNCOMMON", "RARE", "GLORIOUS")
WEIGHT_FLOOR = {1: "COMMON", 2: "COMMON", 3: "COMMON", 4: "RARE", 5: "GLORIOUS"}
WEIGHT_MEANING = {
    1: "everyday vocabulary the era happens to use",
    2: "a descriptive or mechanical word with a clear place",
    3: "thematic vocabulary with real teaching behind it",
    4: "a named judgment, agent, place, patriarch, or event the era turns on",
    5: "a pillar of the set - the act or name the whole story hangs on",
}
HEAVY_BUDGET = 22   # RARE 13 + GLORIOUS 9 slots in a 90-card set
PILLAR_BUDGET = 9   # GLORIOUS slots


def rarity_floor(weight: int) -> str:
    return WEIGHT_FLOOR[int(weight)]


def check_word_weight(weight: Any, rarity: str, rationale: Any) -> list[str]:
    """Issues for a planned card: weight must be 1-5 with a stated reason, and
    the printed rarity may not sit below the weight's floor."""
    issues: list[str] = []
    try:
        w = int(weight)
    except (TypeError, ValueError):
        return ["weight is missing or not an integer (1-5)"]
    if not 1 <= w <= 5:
        return [f"weight={w} is outside 1-5"]
    if not str(rationale or "").strip():
        issues.append("weight_rationale is required: say why the word carries this weight")
    floor = rarity_floor(w)
    if RARITY_ORDER.index(str(rarity).upper()) < RARITY_ORDER.index(floor):
        issues.append(f"word weight {w} ({WEIGHT_MEANING[w]}) requires at least {floor}; printed rarity is {str(rarity).upper()}")
    return issues


def load_series_weights(series_dir: str | Path) -> list[dict[str, Any]]:
    if yaml is None:
        raise RuntimeError("pyyaml is required")
    rows = []
    for meta in sorted(Path(series_dir).glob("cards/*/meta.yml")):
        try:
            m = yaml.safe_load(meta.read_text(encoding="utf-8")) or {}
        except (OSError, ValueError):
            continue
        rows.append({
            "card": meta.parent.name,
            "word": str(m.get("word", "")).upper(),
            "rarity": str(m.get("rarity", "")).upper(),
            "weight": m.get("weight"),
            "weight_rationale": m.get("weight_rationale"),
        })
    return rows


def audit_series(series_dir: str | Path) -> dict[str, Any]:
    rows = load_series_weights(series_dir)
    unweighted = [r["card"] for r in rows if r["weight"] is None]
    violations = []
    heavy = []
    pillars = []
    for r in rows:
        if r["weight"] is None:
            continue
        issues = check_word_weight(r["weight"], r["rarity"], r["weight_rationale"] or "x")
        if issues:
            violations.append({"card": r["card"], "word": r["word"], "rarity": r["rarity"], "weight": r["weight"], "issues": issues})
        if int(r["weight"]) >= 4:
            heavy.append(r["card"])
        if int(r["weight"]) == 5:
            pillars.append(r["card"])
    return {
        "rows": rows,
        "unweighted": unweighted,
        "violations": violations,
        "heavy": heavy,
        "pillars": pillars,
        "heavy_budget": HEAVY_BUDGET,
        "pillar_budget": PILLAR_BUDGET,
    }


__all__ = ["WEIGHT_FLOOR", "WEIGHT_MEANING", "HEAVY_BUDGET", "PILLAR_BUDGET", "rarity_floor", "check_word_weight", "audit_series", "load_series_weights"]
