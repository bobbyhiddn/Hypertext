"""Printed ability text -> an ORDERED list of effect components.

The 7-slot classification vector (COST CORE KICKER CONDITION FILTER INTERACT
TIMING) is a design-time device: it exists so the shape gates can tell two cards
apart. It cannot carry a card that prints three clauses, and roughly a quarter of
the set does - so exporting the game's execution plan from those slots silently
dropped printed effects.

This reads the sentence instead. The ability vocabulary is closed by
schema/ability_grammar.yml, so a scanner over ~25 clause patterns covers all of
it, in printed order, which is also the order the rules require them to resolve.
"""
from __future__ import annotations
import re
from typing import Any, Callable

NUM = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,
       "nine":9,"ten":10,"every":"all","any":"any","a":1,"the":1}
TYPES = "NOUN|VERB|ADJECTIVE|NAME|TITLE"
STATS = "LORE|CONTEXT|COMPLEXITY"


def n(word: str | None, default: int = 1):
    if word is None:
        return default
    w = word.strip().lower()
    if w.isdigit():
        return int(w)
    return NUM.get(w, default)


def _filter(tail: str) -> dict | None:
    """The qualifier attached to a clause: which cards it may touch."""
    t = tail or ""
    m = re.search(rf"\b(?:has|have|each have|with) ({STATS}) (\w+) or more\b", t)
    if m: return {"kind": "stat_floor", "stat": m.group(1), "min": n(m.group(2))}
    m = re.search(rf"\b(?:that is an?|of card type) ({TYPES})\b", t)
    if m: return {"kind": "type", "type": m.group(1)}
    if re.search(r"\bof the named type\b", t): return {"kind": "named_type"}
    if re.search(r"\bcard type is in the Chapter Lot\b", t): return {"kind": "in_lot", "lot": "chapter"}
    if re.search(r"\bcard type is in your Lot\b", t): return {"kind": "in_lot", "lot": "own"}
    if re.search(r"\bcard type not in your Lot\b", t): return {"kind": "not_in_lot", "lot": "own"}
    if re.search(r"\bcard type is in one of your Pages\b", t): return {"kind": "in_page"}
    if re.search(r"\bof that added card's card type\b", t): return {"kind": "same_type", "as": "added"}
    if re.search(r"\bof that revealed card's card type\b", t): return {"kind": "same_type", "as": "revealed"}
    m = re.search(rf"\bof the same ({STATS}) as that revealed card\b", t)
    if m: return {"kind": "same_stat", "stat": m.group(1), "as": "revealed"}
    if re.search(r"\bone card of each card type\b", t): return {"kind": "one_of_each_type"}
    return None


def _dest(t: str) -> str:
    if re.search(r"\bon the bottom of the Tower\b", t): return "tower_bottom"
    if re.search(r"\bon top of the Tower\b", t):        return "tower_top"
    if re.search(r"\binto Sheol\b", t):                 return "sheol"
    return "sheol"


# Each rule is (regex, builder). Scanned left to right; the earliest match wins,
# so more specific patterns must be able to start earlier, not merely be listed first.
def _rules() -> list[tuple[re.Pattern, Callable[[re.Match], dict | None]]]:
    R: list[tuple[str, Callable[[re.Match], dict | None]]] = []

    # -- players and naming
    R.append((r"\b[Cc]hoose another player\b",
              lambda m: {"kind": "choose_player"}))
    R.append((r"\b[Nn]ame a card type\b",
              lambda m: {"kind": "name_type"}))

    # -- looking at the Tower
    R.append((r"\b[Ll]ook at (\w+) card from the top of the Tower and (\w+) card from the bottom of the Tower\b",
              lambda m: {"kind": "look", "n": n(m.group(1)) + n(m.group(2)), "from": "both_ends"}))
    R.append((r"\b[Ll]ook at the (top|bottom) (\w+) cards? of the Tower\b",
              lambda m: {"kind": "look", "n": n(m.group(2)), "from": m.group(1)}))
    R.append((r"\b[Ll]ook at (\w+) card from the (top|bottom) of the Tower\b",
              lambda m: {"kind": "look", "n": n(m.group(1)), "from": m.group(2)}))
    R.append((r"\b[Rr]eveal the top (\w+) cards? of the Tower\b",
              lambda m: {"kind": "look", "n": n(m.group(1)), "from": "top", "public": True}))
    R.append((r"\b[Rr]eveal (\w+) card from the top of the Tower\b",
              lambda m: {"kind": "look", "n": n(m.group(1)), "from": "top", "public": True}))

    # -- taking from what you looked at
    R.append((r"\b(?:A|a)dd (up to )?(\w+) (?:of those|revealed|of the other) cards?((?:(?! to your hand).)*) to your hand",
              lambda m: dict({"kind": "take", "n": n(m.group(2)), "up_to": bool(m.group(1)),
                              "from": "looked"},
                             **({"filter": _filter(m.group(3))} if _filter(m.group(3)) else {}))))
    R.append((r"\badd that revealed card to your hand\b",
              lambda m: {"kind": "take", "n": 1, "from": "looked"}))
    R.append((r"\b[Aa]dd that revealed card to your hand\b",
              lambda m: {"kind": "take", "n": 1, "from": "looked"}))
    R.append((r"\bput that revealed card into Sheol\b",
              lambda m: {"kind": "rest", "to": "sheol"}))

    # -- what happens to the cards you did not take
    R.append((r"\bput (?:the other|each other|those) (?:revealed )?cards?((?:(?!(?:Tower|Sheol)).)*)(?:on the bottom of the Tower|on top of the Tower(?: in any order)?|into Sheol)",
              lambda m: {"kind": "rest", "to": _dest(m.group(0)),
                         "ordered": bool(re.search(r"in any order", m.group(0)))}))
    R.append((r"\bput those cards back on top of the Tower in any order\b",
              lambda m: {"kind": "rest", "to": "tower_top", "ordered": True}))
    R.append((r"\b[Pp]ut (any number of |\w+ of )those cards on the bottom of the Tower\b",
              lambda m: {"kind": "rest", "to": "tower_bottom",
                         "n": ("any" if m.group(1).startswith("any number") else n(m.group(1).split()[0]))}))
    R.append((r"\bput (\w+) of the other cards into Sheol\b",
              lambda m: {"kind": "rest", "to": "sheol", "n": n(m.group(1))}))
    R.append((rf"\bput (\w+) of those cards((?:(?!Tower).)*)on the bottom of the Tower\b",
              lambda m: dict({"kind": "rest", "to": "tower_bottom", "n": n(m.group(1))},
                             **({"filter": _filter(m.group(2))} if _filter(m.group(2)) else {}))))

    # -- straight moves between Tower and hand
    R.append((r"\b(?:A|a)dd (\w+) cards? from the (top|bottom) of the Tower to your hand\b",
              lambda m: {"kind": "add", "n": n(m.group(1)), "from": m.group(2)}))
    R.append((r"\b(?:D|d)raws? (\w+) cards? from the Tower\b",
              lambda m: {"kind": "draw", "n": n(m.group(1))}))
    R.append((r"\b[Pp]ut the top (\w+) cards? of the Tower into Sheol\b",
              lambda m: {"kind": "mill", "n": n(m.group(1))}))
    R.append((r"\b[Pp]ut (\w+) card from the top of the Tower on the bottom of the Tower\b",
              lambda m: {"kind": "shift", "n": n(m.group(1)), "from": "top", "to": "tower_bottom"}))

    # -- Sheol
    R.append((r"\b(?:C|c)hoose (up to )?(\w+) cards? in Sheol((?:(?!add th(?:at|ose) chosen|activate).)*)(?:and )?add th(?:at|ose) chosen cards? to your hand",
              lambda m: dict({"kind": "recover", "n": n(m.group(2)), "up_to": bool(m.group(1))},
                             **({"filter": _filter(m.group(3))} if _filter(m.group(3)) else {}))))
    R.append((r"\badd (up to )?(\w+) cards?((?:(?! from Sheol).)*) from Sheol to your hand\b",
              lambda m: dict({"kind": "recover", "n": n(m.group(2)), "up_to": bool(m.group(1))},
                             **({"filter": _filter(m.group(3))} if _filter(m.group(3)) else {}))))
    R.append((rf"\b[Cc]hoose (\w+) ((?:COMMON|UNCOMMON|RARE|GLORIOUS)) card in Sheol((?:(?!activate).)*)and activate that chosen card\b",
              lambda m: dict({"kind": "activate_sheol", "rarity": m.group(2)},
                             **({"filter": _filter(m.group(3))} if _filter(m.group(3)) else {}))))
    R.append((r"\b[Rr]eturn every card in Sheol to the Tower\b",
              lambda m: {"kind": "reset_tower"}))
    R.append((r"\bshuffle the cards in the Tower\b",
              lambda m: {"kind": "shuffle", "zone": "tower"}))

    # -- your own hand as a cost
    R.append((rf"\b[Dd]iscard (\w+) cards? (of the same card type )?((?:(?!from your hand).)*)from your hand into Sheol\b",
              lambda m: dict({"kind": "discard", "n": n(m.group(1)), "from": "hand", "to": "sheol"},
                             **({"same_type": True} if m.group(2) else {}),
                             **({"filter": _filter(m.group(3))} if _filter(m.group(3)) else {}))))
    R.append((rf"\b(?:P|p)ut (\w+) ({TYPES})? ?(?:other )?(?:cards?)? ?((?:(?!from your hand).)*)from your hand (into Sheol|on the bottom of the Tower|on top of the Tower)",
              lambda m: dict({"kind": "discard" if _dest(m.group(4)) == "sheol" else "bury",
                              "n": n(m.group(1)), "from": "hand", "to": _dest(m.group(4))},
                             **({"filter": {"kind": "type", "type": m.group(2)}} if m.group(2)
                                else ({"filter": _filter(m.group(3))} if _filter(m.group(3)) else {})))))
    R.append((r"\b[Cc]hoose (\w+) card in your hand and put that chosen card on the bottom of the Tower\b",
              lambda m: {"kind": "bury", "n": n(m.group(1)), "from": "hand", "to": "tower_bottom"}))
    R.append((r"\b[Yy]ou may put that card on the bottom of the Tower\b",
              lambda m: {"kind": "rest", "to": "tower_bottom", "optional": True}))
    R.append((r"\b[Dd]iscard (\w+) of your Pages\b",
              lambda m: {"kind": "discard_page", "n": n(m.group(1))}))

    # -- Letters
    R.append((r"\b[Ss]pend (\w+) Letters?\b",
              lambda m: {"kind": "spend_letter", "n": n(m.group(1))}))
    R.append((r"\bgain (\w+) Letters?\b",
              lambda m: {"kind": "gain_letter", "n": n(m.group(1))}))

    # -- other players
    R.append((r"\b[Ee]ach player draws (\w+) cards? from the Tower\b",
              lambda m: {"kind": "each_player", "verb": "draw", "n": n(m.group(1))}))
    R.append((r"\b[Ee]ach player puts every card( of the named type)? from that player's hand into Sheol\b",
              lambda m: dict({"kind": "each_player", "verb": "discard", "n": "all"},
                             **({"filter": {"kind": "named_type"}} if m.group(1) else {}))))
    R.append((r"\beach player puts every card of the named type from that player's hand into Sheol\b",
              lambda m: {"kind": "each_player", "verb": "discard", "n": "all",
                         "filter": {"kind": "named_type"}}))
    R.append((r"\b[Ee]ach player exchanges that player's Lot for a new one from the Lots\b",
              lambda m: {"kind": "exchange_lots", "who": "each"}))
    R.append((r"\b[Ee]ach (?:player|of you) reveals (\w+) card from (?:that player's|your) hand\b",
              lambda m: {"kind": "reveal_hand", "who": "each", "n": n(m.group(1))}))
    R.append((r"\b[Tt]hat chosen player reveals (\w+) card from that player's hand\b",
              lambda m: {"kind": "reveal_hand", "who": "chosen", "n": n(m.group(1))}))
    R.append((rf"\bthat chosen player puts (\w+) (?:cards?|({TYPES}))? ?(?:of the named type )?from that player's hand (into Sheol|on the bottom of the Tower)",
              lambda m: {"kind": "lose_card", "who": "chosen", "n": n(m.group(1)),
                         "to": _dest(m.group(3))}))
    R.append((r"\bthat chosen player spends (\w+) Letters?\b",
              lambda m: {"kind": "lose_letter", "who": "chosen", "n": n(m.group(1))}))
    R.append((r"\bthat chosen player draws (\w+) cards? from the Tower\b",
              lambda m: {"kind": "give_draw", "who": "chosen", "n": n(m.group(1))}))
    R.append((r"\b[Ee]xchange (\w+) card from your hand with (\w+) card from that chosen player's hand\b",
              lambda m: {"kind": "exchange_player", "n": n(m.group(1))}))

    # -- persistent
    R.append((r"\b[Pp]ut this card in front of you\b",
              lambda m: {"kind": "wait"}))

    return [(re.compile(p), b) for p, b in R]


RULES = _rules()

# Clauses that are bookkeeping for an effect already emitted, not effects of
# their own. Listed so the coverage gate can tell "handled" from "dropped".
IGNORED = [
    r"\bthat activated card stays in that Page\b",
    r"\bin any order\b",
    r"\bof the Tower\b",
]


def scan(text: str) -> list[dict[str, Any]]:
    """Every effect in printed order."""
    out, i = [], 0
    while i < len(text):
        best, best_at, best_build = None, len(text), None
        for pat, build in RULES:
            m = pat.search(text, i)
            if m and m.start() < best_at:
                best, best_at, best_build = m, m.start(), build
        if not best:
            break
        eff = best_build(best)
        if eff:
            out.append(eff)
        i = best.end()
    return out


def residue(text: str) -> list[str]:
    """The spans no pattern consumed. Anything meaningful here is a dropped effect."""
    spans, i = [], 0
    while i < len(text):
        best, best_at = None, len(text)
        for pat, _ in RULES:
            m = pat.search(text, i)
            if m and m.start() < best_at:
                best, best_at = m, m.start()
        if not best:
            spans.append(text[i:]); break
        if best.start() > i:
            spans.append(text[i:best.start()])
        i = best.end()
    out = []
    for sp in spans:
        sp = re.sub(r"\b(?:then|and|the|a|an|of|to|your|you|that|those|this|from|"
                    r"in|on|for|with|at|it|is|are|may|card|cards|Tower|hand|"
                    r"chosen|revealed|other|player|players|each|Sheol|Lot|Lots|"
                    r"start|next|turn|any|order|back|new|If|if|or|more|has|have|"
                    r"put|puts|Put|add|Add|draw|draws|Draw|so|but|when|When|"
                    r"one|two|three|four|five|six|seven|eight|nine|ten|every|"
                    r"stays|Page|Pages|activated|activate|records|not|be)\b",
                    " ", sp)
        sp = re.sub(r"[^A-Za-z' ]", " ", sp)
        sp = " ".join(sp.split())
        if sp:
            out.append(sp)
    return out


def _branches(t: str):
    m = re.search(r"\b[Ii]f\b(.*)$", t, re.S)
    if not m:
        return None, None, None
    head = t[:m.start()]
    rest = m.group(1)
    i = rest.find(",")
    if i < 0:
        return None, None, None
    test = rest[:i]
    parts = re.split(r";\s*otherwise,?\s*", rest[i + 1:], maxsplit=1, flags=re.I)
    return head, test, (parts[0], parts[1] if len(parts) > 1 else None)


def _condition(test: str, t: str) -> dict | None:
    m = re.search(rf"\btotal ({STATS}) ([\w-]+) or more\b", test)
    if m:
        return {"kind": "pages_stat_total", "stat": m.group(1),
                "min": 22 if m.group(2).startswith("twenty") else n(m.group(2)),
                "scope": "one_page"}
    m = re.search(rf"\bthat revealed card has ({STATS}) (\w+) or more\b", test)
    if m:
        return {"kind": "revealed_stat", "stat": m.group(1), "min": n(m.group(2))}
    if re.search(r"\bis not the named type\b", test):
        return {"kind": "revealed_named_type", "negated": True}
    if re.search(r"\bis the named type\b", test):
        return {"kind": "revealed_named_type", "negated": False}
    m = re.search(rf"\bthat revealed card is an? ({TYPES})\b", test)
    if m:
        return {"kind": "revealed_type", "type": m.group(1)}
    m = re.search(rf"\bthat drawn card is an? ({TYPES})\b", test)
    if m:
        return {"kind": "drawn_type", "type": m.group(1)}
    m = re.search(rf"\byour revealed card has the higher ({STATS})\b", test)
    if m:
        return {"kind": "duel_stat", "stat": m.group(1)}
    if re.search(r"\bcard type is in the Chapter Lot\b", test):
        return {"kind": "revealed_in_lot"}
    return None


def effects_of(text: str) -> list[dict[str, Any]]:
    """The card's execution plan: effects in printed order, conditionals nested."""
    head, test, branches = _branches(text)
    if not branches:
        return scan(text)
    cond = _condition(test, text)
    if not cond:
        return scan(text)
    met, otherwise = branches
    # anything after the conditional sentence is unconditional again
    tail = ""
    if met and "." in met:
        cut = met.index(".")
        met, tail = met[:cut], met[cut + 1:]
    cond["when_met"] = scan(met or "")
    if otherwise:
        cond["when_not"] = scan(otherwise)
    return scan(head or "") + [cond] + scan(tail)


# "draw one card for each card fewer than four in your hand" scales the draw
# before it, so it is a modifier rather than an effect of its own.
def apply_scaling(effects: list[dict], text: str) -> list[dict]:
    m = re.search(r"\bfor each ([^.;]+)", text, re.I)
    if not m:
        return effects
    for e in reversed(effects):
        if e["kind"] in ("draw", "take", "recover"):
            e["for_each"] = m.group(1).strip()
            break
    return effects
