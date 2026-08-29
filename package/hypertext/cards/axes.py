"""Mechanic axes - which parts of the game an ability actually plays.

User (2026-08-29): "i dont see stats being used in basically any abilities. i
see types and letters occasionally. how could we account for this in our
recipe generation?" At 76 cards, two abilities read a stat, 22 read a type,
six touch Letters, five Lots, three Pages. Every card prints three 1-5 stats;
almost nothing plays them.

An axis is a game surface an ability reads or moves. A card may count on
several. Targets per 90 cards live in series/<series>/set-standards.yml
(`mechanic_axis_targets`) together with per-ten-card batch minimums
(`batch_minimums_per_ten`); `hypertext axis-audit` reports set coverage and
scripts/pipeline/offline_check.py fails a designs module that does not carry
its share of the batch minimums.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

AXES: dict[str, str] = {
    "stats": r"\b(?:LORE|CONTEXT|COMPLEXITY)\b",
    "types": r"\b(?:NOUN|VERB|ADJECTIVE|NAME|TITLE)\b|\bcard type\b|\bnamed type\b",
    "letters": r"\bLetters?\b",
    "lots": r"\bLots?\b|\bChapter Lot\b",
    "pages": r"\bPages?\b",
    "opponent": r"\b(?:another|other|chosen|target|each|every|all) players?\b",
    "sheol": r"\bSheol\b",
}

# The stat an ability reads should rhyme with the word (user, 2026-08-29):
# weight, glory and depth read LORE; multitude, all and many read CONTEXT;
# tongue, name, confusion and foreignness read COMPLEXITY. Recorded here as
# guidance for the seed prompt and the designer; not enforced by regex.
STAT_RHYME = {
    "LORE": "weight, glory, depth, holiness, judgment, promise",
    "CONTEXT": "multitude, all, many, gathering, filling, scattering",
    "COMPLEXITY": "tongue, name, confusion, foreignness, division, speech",
}

DEFAULT_TARGETS = {"stats": 18, "types": 26, "letters": 12, "lots": 10, "pages": 8, "opponent": 16, "sheol": 24}
DEFAULT_BATCH_MINIMUMS = {"stats": 2, "letters": 1, "lots_or_pages": 1}


def classify_axes(ability_text: str) -> set[str]:
    """The axes one printed ability reads or moves."""
    t = " ".join(str(ability_text).split())
    return {axis for axis, pattern in AXES.items() if re.search(pattern, t)}


def load_standards(series_dir: str | Path) -> dict[str, Any]:
    path = Path(series_dir) / "set-standards.yml"
    if yaml is None or not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, ValueError):
        return {}


def axis_targets(series_dir: str | Path) -> dict[str, int]:
    s = load_standards(series_dir)
    return {**DEFAULT_TARGETS, **{k: int(v) for k, v in (s.get("mechanic_axis_targets") or {}).items()}}


def batch_minimums(series_dir: str | Path, batch_size: int) -> dict[str, int]:
    """Minimum cards per axis for a batch of `batch_size`, scaled from the per-ten figures (floor)."""
    s = load_standards(series_dir)
    per_ten = {**DEFAULT_BATCH_MINIMUMS, **{k: int(v) for k, v in (s.get("batch_minimums_per_ten") or {}).items()}}
    return {k: math.floor(v * batch_size / 10) for k, v in per_ten.items()}


def batch_shortfalls(series_dir: str | Path, abilities: Iterable[str]) -> list[str]:
    """Which batch minimums a set of ability texts fails to meet."""
    texts = list(abilities)
    mins = batch_minimums(series_dir, len(texts))
    counts = {"stats": 0, "letters": 0, "lots_or_pages": 0}
    for text in texts:
        axes = classify_axes(text)
        counts["stats"] += "stats" in axes
        counts["letters"] += "letters" in axes
        counts["lots_or_pages"] += bool(axes & {"lots", "pages"})
    return [
        f"batch of {len(texts)} needs at least {need} card(s) on {axis.replace('_', ' ')}; it has {counts[axis]}"
        for axis, need in mins.items()
        if counts[axis] < need
    ]


def load_series_abilities(series_dir: str | Path) -> list[tuple[str, str]]:
    rows = []
    for path in sorted(Path(series_dir).glob("cards/*/card.json")):
        try:
            c = json.loads(path.read_text(encoding="utf-8"))["content"]
            rows.append((path.parent.name, str(c["ABILITY_TEXT"])))
        except (OSError, ValueError, KeyError):
            continue
    return rows


def audit_series(series_dir: str | Path) -> dict[str, Any]:
    rows = load_series_abilities(series_dir)
    targets = axis_targets(series_dir)
    by_axis: dict[str, list[str]] = {axis: [] for axis in AXES}
    for label, text in rows:
        for axis in classify_axes(text):
            by_axis[axis].append(label)
    return {"cards": len(rows), "targets": targets, "by_axis": by_axis}


__all__ = ["AXES", "STAT_RHYME", "classify_axes", "axis_targets", "batch_minimums", "batch_shortfalls", "audit_series", "load_series_abilities"]
