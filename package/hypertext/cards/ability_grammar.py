"""Classify ability copy into the productions of schema/ability_grammar.yml.

The grammar is the finite menu abilities are designed from:

    ABILITY := [COST] CORE [KICKER] [CONDITION] [TIMING]

This module names, for one printed ability, which production fills each slot,
so a series can be audited for coverage ("which cores are unused at RARE?")
and a candidate can be checked against the tiers a production allows. It is
descriptive: an ability the grammar cannot name is reported as `unclassified`,
never rejected - the estimator and the shape/lemma rules do the rejecting.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

GRAMMAR_PATH = Path(__file__).resolve().parents[3] / "schema" / "ability_grammar.yml"


def load_grammar(path: Path = GRAMMAR_PATH) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("pyyaml is required to load the ability grammar")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


_N = r"(?:one|two|three|four|five|up to \w+|any number of)"


def _first(patterns: list[tuple[str, str]], text: str) -> str | None:
    for name, pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return name
    return None


def classify(text: str) -> dict[str, Any]:
    """Name the productions an ability uses. Every slot may be None."""
    t = " ".join(str(text).split())
    low = t.lower()

    cost = _first([
        ("discard_page", r"\bdiscard one of your Pages\b|\bput every card in one of your Pages into Sheol\b"),
        ("spend_letter", r"(?:^|[.;]\s*)spend\s+(?:one|two|three|a)\s+Letters?\b"),
        ("discard_n", rf"\bdiscard\s+{_N}\s+cards?\s+from your hand"),
        ("bury_hand_card", r"(?:^|[.;]\s*)(?:choose one card in your hand and )?put\s+(?:one|that chosen)\s+(?:[A-Z]+\s+)?card\s+(?:from your hand\s+)?on the bottom of the Tower"),
    ], t)

    core = _first([
        ("move_lot", r"\bexchange\s+your Lot\b|\breturn\s+your Lot\b"),
        ("activate_sheol", r"\bactivate\s+that chosen card\b"),
        ("reset_tower", r"\breturn\s+every card in Sheol to the Tower\b"),
        ("scale_structure", r"\bone card (?:of|for) each card type in (?:that chosen Page|the Chapter Lot|your Lot|another player's Lot|that chosen player's Lot)\b"),
        ("return_from_page", r"\breturn\s+one card from (?:one of )?your Pages?\b"),
        ("return_to_tower", r"\breturn\s+those chosen cards to the top of the Tower\b"),
        ("exchange_player", r"\bexchange\s+one card from your hand with one card from that chosen player's hand\b"),
        ("exchange_sheol", r"\bexchange\s+(?:up to \w+ )?cards? from your hand with\b"),
        ("recover", rf"\bchoose\s+{_N}\s+cards?\s+in Sheol\b.*\badd\s+(?:that|those)\s+chosen|\badd\s+{_N}\s+cards?\s+from Sheol to your hand\b"),
        ("mill_take", r"\bput the top \w+ cards of the Tower into Sheol\.?,? (?:then )?add (?:one|up to \w+) of those cards\b"),
        ("reveal_test", r"\breveal one card from the top of the Tower\b.*\bIf that revealed card\b"),
        ("reveal_take", r"\breveal one card from the top of the Tower and add that revealed card to your hand\b"),
        ("look_take", r"\b(?:look at|reveal) (?:the )?(?:top|bottom|one card from the top)\b.*\badd (?:one|up to \w+)(?: of those cards| of those cards that [^.;]*| revealed cards? of the named type| revealed cards? whose card type is in [^.;]*?)? to your hand\b|\blook at one card from the top of the Tower and one card from the bottom of the Tower\. Add one of those cards"),
        ("gain_letter", r"(?:^|[.;]\s*(?:then\s+)?)gain\s+(?:one|two|three|four|five|a)\s+Letters?\b"),
        ("add_bottom", r"\badd one card from the bottom of the Tower to your hand\b"),
        ("add_top", r"\badd one card from the top of the Tower to your hand\b"),
        ("draw", r"\bdraws?\s+(?:one|two|three)\s+cards?\s+from the Tower\b"),
    ], t)

    interact = _first([
        ("every_material", r"\b(?:each|every|all)\s+(?:other\s+)?players?\s+(?:draws?|adds?|discards?|puts?|spends?|gains?)\b"),
        ("every_reveals", r"\b(?:each|every|all)\s+(?:other\s+)?players?\s+(?:reveals?|names?|looks?)\b"),
        ("lose_letter", r"\bthat chosen player spends\b"),
        ("lose_card", r"\bthat chosen player (?:puts|discards)\b"),
        ("reveal_hand", r"\bthat chosen player reveals\b"),
        ("read_page", r"\bPage belonging to another player\b|\banother player's Lot\b|\bthat chosen player's Lot\b"),
    ], t)

    kicker = _first([
        ("draw_one_more", r"[.;]\s*(?:then\s+)?draw one card from the Tower\.?$|\bthen draw one card from the Tower\b"),
        ("shuffle", r"\bshuffle the cards in the Tower\b"),
        ("reorder", r"\bput those cards back on top of the Tower in any order\b"),
        ("rest_sheol", r"\bput the other (?:revealed )?cards? into Sheol\b"),
        ("rest_top", r"\bput (?:the other|each other revealed) cards? on top of the Tower(?: in any order)?\b"),
        ("rest_bottom", r"\bput the other cards? on the bottom of the Tower\b|\bput any number of those cards on the bottom of the Tower\b"),
        ("bury_looked", r"\byou may put that card on the bottom of the Tower\b"),
        ("bury_hand", r"\bthen you may put one (?:other )?card (?:of [^.;]*?)?from your hand on the bottom of the Tower\b"),
        ("name_type", r"\bname a card type\b"),
        ("peek", r"\b(?:then )?look at one card from the top of the Tower\b(?!.*add one of those)"),
        ("reveal_next", r"\bthen reveal one card from the top of the Tower\b"),
    ], t)

    filt = _first([
        ("in_lot", r"\bcard type is in (?:the Chapter Lot|your Lot)\b"),
        ("stat_floor", r"\b(?:LORE|CONTEXT|COMPLEXITY)\s+(?:one|two|three|four|five)\s+or more\b"),
        ("named_type", r"\bof the named type\b|\bnot the named type\b"),
        ("same_type", r"\bsame card type\b|\bthat added card's card type\b"),
        ("type", r"\b(?:is|no)\s+(?:a\s+)?(?:NOUN|VERB|ADJECTIVE|NAME|TITLE)\b|\bone (?:NOUN|VERB|ADJECTIVE|NAME|TITLE) from your hand\b"),
    ], t)

    condition = _first([
        ("pages_threshold", r"\bat least \w+ cards in Pages\b"),
        ("revealed_in_lot", r"\bIf that revealed card's card type is in\b"),
        ("revealed_is_type", r"\bIf that revealed card is\b"),
        ("hand_lacks_type", r"\bIf no (?:NOUN|VERB|ADJECTIVE|NAME|TITLE) is in your hand\b"),
        ("for_each", r"\bfor each\b"),
        ("otherwise", r"\botherwise\b"),
        ("if", r"\bif\b"),
    ], t)

    timing = "next_turn" if re.search(r"\bat the start of your next turn\b", low) else "now"
    return {"cost": cost, "core": core, "interact": interact, "kicker": kicker, "filter": filt, "condition": condition, "timing": timing, "unclassified": core is None}


def load_series_abilities(series_dir: str | Path) -> list[tuple[str, str, str]]:
    rows = []
    for path in sorted(Path(series_dir).glob("cards/*/card.json")):
        try:
            c = json.loads(path.read_text(encoding="utf-8"))["content"]
            rows.append((path.parent.name, str(c["RARITY_TEXT"]).upper(), c["ABILITY_TEXT"]))
        except (OSError, ValueError, KeyError):
            continue
    return rows


def coverage(series_dir: str | Path) -> dict[str, Any]:
    """Which cores each tier uses, and which grammar cores it has not used."""
    grammar = load_grammar()
    cores = list(grammar["productions"]["CORE"].keys())
    used: dict[str, dict[str, list[str]]] = {}
    unclassified: list[tuple[str, str]] = []
    for label, rarity, text in load_series_abilities(series_dir):
        c = classify(text)
        if c["unclassified"]:
            unclassified.append((label, text))
            continue
        used.setdefault(rarity, {}).setdefault(c["core"], []).append(label)
    return {"cores": cores, "used": used, "unclassified": unclassified}


__all__ = ["classify", "coverage", "load_grammar", "load_series_abilities", "GRAMMAR_PATH"]
