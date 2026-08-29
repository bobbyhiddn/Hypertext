"""No two cards share an ability shape.

User (2026-08-28): "We aren't being creative enough with abilities. I think
HOVER does the same thing as KINGDOM." HOVER v1 was "each player draws one,
then add up to three from Sheol"; KINGDOM is "each player adds one from Sheol,
then add up to three from Sheol". Same core motion, different verb.

The shape of an ability is its core motion - the biggest material gain and
where it comes from - plus the qualifiers that make it a different play:

  core      the acquisitive verb, its source zone and quantity class
  reach     touches every player / targets another player
  look      how many cards are looked at or revealed first
  filter    a type, stat, or structure filter on what is taken
  cost      something paid before the payoff (spend, put into Sheol, discard)
  branch    a printed condition
  rest      where the untaken cards go (top in any order / bottom / Sheol)
  zones     every zone the copy names

Two abilities with the same signature are the same card with different
words and are rejected in the plan phase; `hypertext ability-audit --series`
lists every pair. The signature is deliberately coarse on wording and fine
on play: HIGH (look at two, take one, other to the bottom) and TONGUE (look
at three, take one, others to the bottom) differ on `look`; DEEP (three from
Sheol with a COMPLEXITY filter) and REDEEMER (spend a Letter, three from
Sheol) differ on `filter` and `cost`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

_QTY = {
    "one": "1", "a": "1", "an": "1", "the top card": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
}
_ACQ = r"(?:draws?|adds?|gains?|returns?|exchanges?)"
_ZONE = r"(?:Tower|Sheol|hand|Pages?|Lots?|Chapter Lot)"
_STAT_OR_TYPE = r"(?:LORE|CONTEXT|COMPLEXITY|NOUN|VERB|ADJECTIVE|NAME|TITLE|card type)"


def _quantity(text: str) -> str:
    text = text.strip().lower()
    if text.startswith("up to "):
        return "up-to-" + _QTY.get(text[6:].split()[0], text[6:].split()[0])
    if text.startswith("any number"):
        return "any"
    return _QTY.get(text.split()[0], text.split()[0]) if text else "1"


def _core(t: str, look_zone: str | None) -> dict[str, Any]:
    """The biggest material gain: (verb, source zone, quantity class)."""
    candidates: list[tuple[int, dict[str, Any]]] = []
    rank = lambda q: {"up-to-5": 7, "5": 7, "up-to-4": 6, "4": 6, "up-to-3": 5, "3": 5, "any": 4, "up-to-2": 3, "2": 3, "up-to-1": 1, "1": 1}.get(q, 2)
    # (a) "draw two cards from the Tower", "add one card from the bottom of the Tower", "gain one Letter"
    for m in re.finditer(rf"\b({_ACQ})\s+((?:up to\s+|any number of\s+)?(?:one|two|three|four|five|six|seven|eight|nine|ten|a|an))\s+(?:cards?|Letters?|card of each)(?:[^.;]*?\bfrom\s+(?:the\s+)?(?:top of the\s+|bottom of the\s+)?({_ZONE}))?", t, re.IGNORECASE):
        verb = re.sub(r"s$", "", m.group(1).lower()); qty = _quantity(m.group(2))
        zone = "Letters" if verb == "gain" else (m.group(3) or "")
        candidates.append((rank(qty), {"verb": verb, "zone": zone, "qty": qty}))
    # (b) "choose up to three cards in Sheol ... add those chosen cards"
    for m in re.finditer(rf"\bchoose\s+((?:up to\s+)?(?:one|two|three|four|five))\s+cards?\s+in\s+({_ZONE})", t, re.IGNORECASE):
        if re.search(r"\badd\s+(?:that|those)\s+chosen\s+cards?", t, re.IGNORECASE):
            qty = _quantity(m.group(1)); candidates.append((rank(qty), {"verb": "add", "zone": m.group(2), "qty": qty}))
    # (c) "add one of those cards", "add that revealed card", "add up to one of those cards" after a look/reveal
    for m in re.finditer(r"\badd\s+((?:up to\s+)?(?:one|two|three|any number))\s+(?:of those|revealed)\s+cards?|\badd\s+that\s+revealed\s+card|\badd\s+one\s+revealed\s+card", t, re.IGNORECASE):
        qty = _quantity(m.group(1)) if m.group(1) else "1"
        candidates.append((rank(qty), {"verb": "add", "zone": look_zone or "Tower", "qty": qty}))
    if not candidates:
        return {"verb": None, "zone": None, "qty": None}
    best = max(candidates, key=lambda c: c[0])[1]
    best["zone"] = (best["zone"] or "").title() if (best["zone"] or "").lower() not in ("hand", "letters") else best["zone"].lower().title()
    return best


def _filter_kind(t: str, low: str) -> str | None:
    """WHICH kind of filter narrows the take, not merely whether one does.

    A Chapter-Lot filter and a NAME filter are different plays, and with a dozen
    look-and-take COMMONs in the set a single boolean makes unrelated cards
    collide on look count and destination alone.
    """
    if re.search(r"\b(?:LORE|CONTEXT|COMPLEXITY)\b", t):
        return "same" if re.search(r"\bsame (?:LORE|CONTEXT|COMPLEXITY)\b", t) else "stat"
    # Your Lot, the shared Chapter Lot and another player's Lot are three different
    # objects in the rules, so reading one is not the same play as reading another.
    if re.search(r"\bChapter Lot\b", t, re.IGNORECASE):
        return "lot:chapter"
    if re.search(r"\b(?:another player's|that chosen player's) Lot\b", t, re.IGNORECASE):
        return "lot:other"
    if re.search(r"\byour Lot\b|\bcard type is (?:not )?in\b|\bcard type not in\b", t, re.IGNORECASE):
        return "lot:own"
    if "same card type" in low or "each card type" in low:
        return "same"
    if re.search(r"\bnamed type\b", low):
        return "named"
    if re.search(r"\b(?:NOUN|VERB|ADJECTIVE|NAME|TITLE)\b", t) or "card type" in low:
        return "type"
    return None


def ability_signature(text: str) -> dict[str, Any]:
    """Structured shape of one ability's printed copy."""
    t = " ".join(str(text).split())
    low = t.lower()
    look = re.search(rf"\b(?:look at|reveal)\s+(?:the\s+)?(?:top\s+|bottom\s+)?(one|two|three|four|five|any number of)?\s*(?:cards?|card)?(?:\s+(?:from|of)\s+(?:the\s+)?(?:top of the\s+|bottom of the\s+)?({_ZONE}))?", t, re.IGNORECASE)
    look_n = _quantity(look.group(1) or "one") if look else "0"
    look_zone = (look.group(2) if look else None) or ("Tower" if look else None)
    core = _core(t, look_zone)
    verbs = set(re.sub(r"s$", "", v.lower()) for v in re.findall(rf"\b({_ACQ})\b", t, re.IGNORECASE))
    # A draw and an add are both "a card"; a gift to every player is part of the
    # reach, not a second motion (HOVER v1 "each player draws one" = KINGDOM
    # "each player adds one").
    kind = lambda v: "card" if v in ("draw", "add") else v
    every = bool(re.search(r"\b(?:each|every|all) players?\b", low))
    secondary = sorted({kind(v) for v in verbs if v != core["verb"]} - ({kind(core["verb"])} if core["verb"] else set()) - ({"card"} if every else set()))
    # Taking or looking from the bottom is a different play from the top; a
    # "put ... on the bottom" placement is not.
    bottom = bool(re.search(r"\b(?:look at|reveal)\s+(?:the\s+)?bottom\b|\b(?:add|draw)\s+[^.;]*?\bfrom the bottom of the Tower\b|\bone card from the bottom of the Tower\b", t, re.IGNORECASE))
    opp = "none"
    m = re.search(r"\b(?:that|the)\s+chosen\s+player\s+(puts?|spends?|discards?|draws?|returns?)\b[^.;]*?(into Sheol|Letters?|bottom of the Tower|top of the Tower|from the Tower)?", t, re.IGNORECASE)
    if m:
        opp = (m.group(1).lower().rstrip("s")) + ":" + ((m.group(2) or "").lower().replace(" ", "-") or "card")
    # Where the untaken cards go is what distinguishes two otherwise identical
    # looks, so the phrasing "each other REVEALED card" must match too.
    _REST = r"\b(?:other|those|remaining)\s+(?:revealed\s+|looked\s+|chosen\s+)?cards?\b[^.;]*"
    rest = "none"
    if re.search(_REST + r"\bbottom of the Tower", t, re.IGNORECASE):
        rest = "bottom"
    elif re.search(_REST + r"\btop of the Tower", t, re.IGNORECASE):
        rest = "top"
    elif re.search(_REST + r"\binto Sheol", t, re.IGNORECASE):
        rest = "sheol"
    put_from = "none"
    if re.search(r"\bput\s+(?:one|two|any number of|up to \w+)\s+(?:other\s+)?cards?\s+(?:of[^.;]*?)?from your hand", t, re.IGNORECASE):
        put_from = "hand"
    elif re.search(r"\bput\s+(?:that|those)\s+(?:card|cards|chosen card|chosen cards)\b", t, re.IGNORECASE) or re.search(r"\bput\s+(?:one|any number)\s+of those cards", t, re.IGNORECASE):
        put_from = "looked"
    return {
        "core": core,
        "every_player": every,
        "bottom": bottom,
        "another_player": bool(re.search(r"\b(?:another|other|chosen|target) player\b", low)),
        "look": look_n,
        "filter": _filter_kind(t, low),
        "cost": bool(re.search(r"\bspend\b", low)) or bool(re.search(r"\b(?:put|discard)\s+[^.;]*?\b(?:from your hand)\b[^.;]*?\binto Sheol\b", t, re.IGNORECASE)),
        "branch": bool(re.search(r"\b(?:if|unless|otherwise)\b", low)),
        "rest": rest,
        "put_from": put_from,
        "secondary": secondary,
        "opponent": opp,
        "shuffle": "shuffle" in low,
        "delayed": bool(re.search(r"\bnext turn\b|\bstart of your next\b", low)),
    }


def signature_key(sig: dict[str, Any]) -> str:
    c = sig["core"]
    return "|".join([
        f"{c['verb']}:{c['zone']}:{c['qty']}",
        "every" if sig["every_player"] else ("other" if sig["another_player"] else "self"),
        f"look{sig['look']}" + ("@bottom" if sig.get("bottom") else ""),
        f"filter:{sig['filter']}" if sig["filter"] else "-",
        "cost" if sig["cost"] else "-",
        "branch" if sig["branch"] else "-",
        f"rest:{sig['rest']}",
        f"put:{sig['put_from']}",
        "+" + ",".join(sig["secondary"]) if sig["secondary"] else "-",
        f"opp:{sig['opponent']}",
        "shuffle" if sig["shuffle"] else "-",
        "delayed" if sig["delayed"] else "-",
    ])


def shape_conflicts(ability_text: str, existing: Iterable[tuple[str, str]]) -> list[dict[str, str]]:
    """Existing (label, ability_text) pairs whose shape equals the candidate's."""
    key = signature_key(ability_signature(ability_text))
    out = []
    for label, other in existing:
        if signature_key(ability_signature(other)) == key:
            out.append({"with": label, "shape": key, "detail": other})
    return out


def load_series_abilities(series_dir: str | Path, *, skip: str | None = None) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for path in sorted(Path(series_dir).glob("cards/*/card.json")):
        label = path.parent.name
        if skip and label == skip:
            continue
        try:
            rows.append((label, json.loads(path.read_text(encoding="utf-8"))["content"]["ABILITY_TEXT"]))
        except (OSError, ValueError, KeyError):
            continue
    return rows


def audit_series(series_dir: str | Path) -> list[dict[str, Any]]:
    rows = load_series_abilities(series_dir)
    groups: dict[str, list[str]] = {}
    for label, text in rows:
        groups.setdefault(signature_key(ability_signature(text)), []).append(label)
    return [{"shape": key, "cards": labels} for key, labels in groups.items() if len(labels) > 1]


__all__ = ["ability_signature", "signature_key", "shape_conflicts", "audit_series", "load_series_abilities"]
