"""Mechanic axes - which parts of the game an ability actually plays.

User (2026-08-29): "i dont see stats being used in basically any abilities. i
see types and letters occasionally. how could we account for this in our
recipe generation?" Two of 76 abilities read a stat although every card prints
three; the grammar had one stat production and nothing asked a batch to use it.

An axis is a game element the printed copy reads or moves: the three STATS,
the five card TYPES, LETTERS, LOTS (a player's Lot or the Chapter Lot), PAGES,
another player (OPPONENT), and SHEOL. A card may count on several axes. Set
targets live in series/<series>/set-standards.yml `mechanic_axis_targets`
(cards of 90); per-batch minimums in `mechanic_axis_batch_minimums` (per ten
cards designed together). The offline check fails a designs module that misses
its minimums; `hypertext axis-audit` reports set coverage against the targets.
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

AXES: dict[str, re.Pattern[str]] = {
    "stats": re.compile(r"\b(?:LORE|CONTEXT|COMPLEXITY)\b"),
    "types": re.compile(r"\b(?:NOUN|VERB|ADJECTIVE|NAME|TITLE)\b|\bcard type\b|\bnamed type\b"),
    "letters": re.compile(r"\bLetters?\b"),
    "lots": re.compile(r"\bLots?\b|\bChapter Lot\b"),
    "pages": re.compile(r"\bPages?\b"),
    "opponent": re.compile(r"\b(?:another|other|chosen|target)\s+player\b|\b(?:each|every)\s+(?:other\s+)?player\b", re.IGNORECASE),
    "sheol": re.compile(r"\bSheol\b"),
}
COMBINED = {"lots_or_pages": ("lots", "pages")}

DEFAULT_TARGETS = {"stats": 18, "types": 26, "letters": 12, "lots": 10, "pages": 8, "opponent": 16, "sheol": 24}
DEFAULT_BATCH_MINIMUMS = {"stats": 2, "letters": 1, "lots_or_pages": 1, "opponent": 1}

# The stat an ability reads should rhyme with the word: weight, glory, depth,
# height and judgment words read LORE; multitude, all, many, filled, scattered
# and nation words read CONTEXT; tongue, name, confusion, foreign and speech
# words read COMPLEXITY. Advisory in the seed prompt; reported by the audit.
STAT_RHYME = {
    "LORE": r"weight|glory|glorious|deep|high|heaven|holy|righteous|wicked|judg|curse|bless|covenant|grace|spirit|faith|redeem|sacrific|altar|blood|great|mighty|one\b",
    "CONTEXT": r"multipl|many|all\b|every|fill|scatter|nation|people|seed|gather|number|star|dust|sand|earth|city|build|brick|flood|water",
    "COMPLEXITY": r"tongue|name|confus|babel|babble|foreign|speak|speech|word|language|hear|call|write|letter",
}


def axes_of(ability_text: str) -> set[str]:
    text = " ".join(str(ability_text).split())
    return {axis for axis, pattern in AXES.items() if pattern.search(text)}


def stats_read(ability_text: str) -> list[str]:
    return sorted(set(re.findall(r"\b(LORE|CONTEXT|COMPLEXITY)\b", str(ability_text))))


def stat_rhyme(word: str, gloss: str = "") -> str | None:
    """The stat whose vocabulary matches the word or its gloss, if any."""
    probe = f"{word} {gloss}".lower()
    for stat, pattern in STAT_RHYME.items():
        if re.search(pattern, probe):
            return stat
    return None


def load_standards(series_dir: str | Path) -> dict[str, Any]:
    path = Path(series_dir) / "set-standards.yml"
    if yaml is None or not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, ValueError):
        return {}


def targets_for(series_dir: str | Path) -> dict[str, int]:
    raw = load_standards(series_dir).get("mechanic_axis_targets") or {}
    return {k: int(raw.get(k, v)) for k, v in DEFAULT_TARGETS.items()}


def batch_minimums_for(series_dir: str | Path) -> dict[str, int]:
    raw = load_standards(series_dir).get("mechanic_axis_batch_minimums") or {}
    return {k: int(raw.get(k, v)) for k, v in DEFAULT_BATCH_MINIMUMS.items()}


def _count(axis: str, axis_sets: Iterable[set[str]]) -> int:
    members = COMBINED.get(axis, (axis,))
    return sum(1 for s in axis_sets if any(m in s for m in members))


def batch_issues(ability_texts: list[str], series_dir: str | Path) -> list[str]:
    """Issues for a designs module: minimums scale with the batch size (per ten cards, rounded up)."""
    n = len(ability_texts)
    if n == 0:
        return []
    sets = [axes_of(t) for t in ability_texts]
    scale = max(1, math.ceil(n / 10))
    issues = []
    for axis, per_ten in batch_minimums_for(series_dir).items():
        need = per_ten * scale
        have = _count(axis, sets)
        if have < need:
            issues.append(f"batch of {n} reads {axis} on {have} card(s); at least {need} required")
    return issues


def load_series_axes(series_dir: str | Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(Path(series_dir).glob("cards/*/card.json")):
        try:
            c = json.loads(path.read_text(encoding="utf-8"))["content"]
        except (OSError, ValueError, KeyError):
            continue
        rows.append({"card": path.parent.name, "word": str(c.get("WORD", "")), "rarity": str(c.get("RARITY_TEXT", "")).upper(),
                     "axes": axes_of(c.get("ABILITY_TEXT", "")), "stats": stats_read(c.get("ABILITY_TEXT", "")),
                     "rhyme": stat_rhyme(c.get("WORD", ""), c.get("GLOSS", ""))})
    return rows


def audit_series(series_dir: str | Path) -> dict[str, Any]:
    rows = load_series_axes(series_dir)
    targets = targets_for(series_dir)
    sets = [r["axes"] for r in rows]
    counts = {axis: _count(axis, sets) for axis in targets}
    mismatched = [r for r in rows if r["stats"] and r["rhyme"] and r["rhyme"] not in r["stats"]]
    return {"rows": rows, "targets": targets, "counts": counts, "total": len(rows), "rhyme_mismatches": mismatched}


__all__ = ["AXES", "axes_of", "stats_read", "stat_rhyme", "batch_issues", "audit_series", "targets_for", "batch_minimums_for", "load_series_axes"]
