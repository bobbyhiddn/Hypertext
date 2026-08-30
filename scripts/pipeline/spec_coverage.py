#!/usr/bin/env python3
"""Does every effect the card PRINTS survive extraction into its spec?

The digital game runs on the exported component vectors, not on the printed
prose, so anything the extractor drops is an ability that silently does less
than the card says. This walks the printed text for effect phrases and asserts
each one has a component behind it.

Usage: spec_coverage.py [--quiet]   (exit 1 if anything is uncovered)
"""
from __future__ import annotations
import json, pathlib, re, sys

sys.path.insert(0, "package"); sys.path.insert(0, "scripts/pipeline")
import export_specs as X

SERIES = pathlib.Path("series/2026-Q1")

# printed phrase -> the component kinds that could be carrying it
RULES: list[tuple[str, tuple[str, ...]]] = [
    (r"\bgain (\w+) Letters?\b",                 ("gain_letter",)),
    (r"\bSpend (\w+) Letters?\b",                ("spend_letter",)),
    (r"\bloses (\w+) Letters?\b",                ("lose_letter",)),
    (r"\bdraws? (\w+) cards? from the Tower\b",  ("draw", "add", "for_each", "each_player",
                                                  "give_draw")),
    (r"\bon the bottom of the Tower\b",          ("bury", "rest", "lose_card", "look_take",
                                                  "shift")),
    (r"\binto Sheol\b",                          ("discard", "reveal_take", "reveal_test",
                                                  "mill_take", "mill", "lose_card",
                                                  "discard_page", "each_player", "rest")),
    (r"\bshuffle\b",                             ("shuffle", "reset_tower")),
    (r"\bName a card type\b",                    ("name_type",)),
    (r"\bLook at the (?:top|bottom)\b",          ("look_take", "peek", "mill_take", "look")),
    (r"\bcards? in Sheol\b",                     ("recover", "activate_sheol", "scale_structure",
                                                  "mill_take", "reset_tower")),
    (r"\bexchanges that player's Lot\b",         ("exchange_lots",)),
    (r"\bDiscard one of your Pages\b",           ("discard_page",)),
    (r"\breveals? one card from (?:that player's|your) hand\b",
                                                 ("reveal_hand", "stat_duel", "exchange_player")),
    (r"\bin front of you\b",                     ("wait",)),
    (r"\bfor each\b",                            ("for_each", "scale_structure", "draw",
                                                  "take", "recover")),
    (r"\bactivate\b",                            ("activate_sheol", "wait")),
    (r"\bexchanges? (?:one|a) card\b",           ("exchange_player",)),
    (r"\bAdd (\w+) cards? from the (?:top|bottom) of the Tower\b", ("add",)),
    (r"\bReveal the top\b",                      ("look", "look_take", "mill_take")),
    (r"\bChoose another player\b",               ("choose_player", "lose_card", "lose_letter",
                                                  "reveal_hand", "stat_duel", "exchange_player",
                                                  "give_draw", "each_player")),
]


def kinds(spec: dict) -> set[str]:
    """Every component kind in a spec, including branch consequents."""
    out: set[str] = set()
    def walk(v):
        if isinstance(v, dict):
            if "kind" in v and isinstance(v["kind"], str):
                out.add(v["kind"])
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    for slot in ("cost", "interact", "core", "kicker", "condition", "persistent",
                 "filter", "effects"):
        walk(spec.get(slot))
    return out


def main() -> int:
    quiet = "--quiet" in sys.argv
    gaps = []
    n = 0
    for p in sorted(SERIES.glob("cards/*/card.json")):
        c = json.loads(p.read_text(encoding="utf-8"))["content"]
        t = c["ABILITY_TEXT"]
        spec = X.spec_for(c)
        have = kinds(spec)
        n += 1
        for pattern, wanted in RULES:
            if re.search(pattern, t, re.I) and not (have & set(wanted)):
                gaps.append((c["NUMBER"], c["WORD"], pattern, t))
    if gaps:
        print(f"{len(gaps)} printed effects with no component, across {n} cards:\n")
        for num, word, pattern, t in gaps:
            print(f"  #{num} {word}: no component for /{pattern}/\n      {t}\n")
        return 1
    if not quiet:
        print(f"spec coverage: {n}/{n} cards - every printed effect has a component")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
