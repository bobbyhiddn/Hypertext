"""Turn each printed ability into an executable component vector.

The grammar already says what a card IS - [COST] CORE [KICKER] [CONDITION] [TIMING]
plus FILTER and INTERACT - and classify() names which production fills each slot.
What it cannot give is the parameters: it knows SHEPHERD is a look_take with
rest_top, not the "3" or the "top", because those live only in the sentence.

This reads the parameters out of the printed copy once, so that from here the spec
is the truth and the prose is a field beside it.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from hypertext.cards import ability_grammar as ag
import effects as FX

ROOT = Path(__file__).resolve().parents[2]
SERIES = Path("series/2026-Q1")
NUM = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10,
       "twelve":12,"fifteen":15,"twenty":20,"twenty-two":22,"a":1,"an":1}

def n(word: str, default=None):
    return NUM.get(str(word).strip().lower(), default)

def cost_of(t: str):
    m = re.search(r"\bSpend (\w+) Letters?\b", t, re.I)
    if m: return {"kind":"spend_letter", "n":n(m.group(1),1)}
    m = re.search(r"\bDiscard (\w+) cards? from your hand into Sheol\b", t, re.I)
    if m: return {"kind":"discard", "n":n(m.group(1),1), "from":"hand", "to":"sheol"}
    m = re.search(r"\bDiscard (\w+) card with ([A-Z]+) (\w+) or more from your hand into Sheol\b", t, re.I)
    if m: return {"kind":"discard", "n":n(m.group(1),1), "from":"hand", "to":"sheol",
                  "filter":{"stat":m.group(2), "min":n(m.group(3))}}
    if re.search(r"\bDiscard one of your Pages\b", t, re.I): return {"kind":"discard_page", "n":1}
    m = re.search(r"^Put (\w+) card from your hand on the bottom of the Tower", t, re.I)
    if m: return {"kind":"bury", "n":n(m.group(1),1), "from":"hand", "to":"tower_bottom"}
    # ENOCH words the same cost as a choice: "Choose one card in your hand and put
    # that chosen card on the bottom of the Tower, then draw two cards."
    m = re.search(r"\bChoose (\w+) card in your hand and put that chosen card "
                  r"on the bottom of the Tower\b", t, re.I)
    if m: return {"kind":"bury", "n":n(m.group(1),1), "from":"hand", "to":"tower_bottom"}
    return None

def filter_of(t: str):
    m = re.search(r"\b(?:that (?:each )?ha(?:s|ve)|with) ([A-Z]+) (\w+) or more\b", t)
    if m: return {"kind":"stat_floor", "stat":m.group(1), "min":n(m.group(2))}
    if re.search(r"\bcard type is in the Chapter Lot\b", t, re.I): return {"kind":"in_lot", "lot":"chapter"}
    if re.search(r"\bcard type is in your Lot\b", t, re.I): return {"kind":"in_lot", "lot":"own"}
    if re.search(r"\bcard type not in your Lot\b", t, re.I): return {"kind":"not_in_lot", "lot":"own"}
    if re.search(r"\bcard type is in one of your Pages\b", t, re.I): return {"kind":"in_page"}
    if re.search(r"\bof the named type\b", t, re.I): return {"kind":"named_type"}
    m = re.search(r"\bsame ([A-Z]+) as\b", t)
    if m: return {"kind":"same_stat", "stat":m.group(1)}
    if re.search(r"\bsame card type\b|\bthat added card's card type\b", t, re.I): return {"kind":"same_type"}
    m = re.search(r"\bthat is an? (NOUN|VERB|ADJECTIVE|NAME|TITLE)\b|\bone (NOUN|VERB|ADJECTIVE|NAME|TITLE) from your hand\b", t)
    if m: return {"kind":"type", "type":(m.group(1) or m.group(2))}
    return None

def core_of(t: str, kind: str):
    if kind == "look_take":
        # WATCHMAN looks at one card from EACH end, so the single-source regex misses it
        if re.search(r"\bone card from the top of the Tower and one card from the bottom of the Tower\b", t, re.I):
            return {"kind":"look_take", "look":2, "from":"both_ends", "take":1, "up_to":False}
        m = re.search(r"\b(?:Look at|Reveal) (?:the )?(top|bottom) (\w+) cards?\b", t, re.I)
        look, frm = (n(m.group(2)), m.group(1).lower()) if m else (None, "top")
        if look is None:   # "Look at one card from the top of the Tower"
            m1 = re.search(r"\b(?:Look at|Reveal) (\w+) cards? from the (top|bottom) of the Tower\b", t, re.I)
            if m1: look, frm = n(m1.group(1), 1), m1.group(2).lower()
        m2 = re.search(r"\bAdd (?:up to )?(\w+) (?:of those|revealed)", t, re.I)
        take = n(m2.group(1), 1) if m2 else 1
        upto = bool(re.search(r"\bAdd up to\b", t, re.I))
        return {"kind":"look_take", "look":look, "from":frm, "take":take, "up_to":upto}
    if kind == "draw":
        m = re.search(r"\bdraws? (?:up to )?(\w+) cards? from the Tower\b", t, re.I)
        return {"kind":"draw", "n":n(m.group(1),1) if m else 1}
    if kind == "recover":
        m = re.search(r"\b(?:Choose|add) (?:up to )?(\w+) cards? (?:in|from) Sheol\b", t, re.I)
        return {"kind":"recover", "n":n(m.group(1),1) if m else 1,
                "up_to":bool(re.search(r"up to \w+ cards? (?:in|from) Sheol", t, re.I))}
    if kind == "gain_letter":
        m = re.search(r"\bgain (\w+) Letters?\b", t, re.I)
        return {"kind":"gain_letter", "n":n(m.group(1),1) if m else 1}
    if kind in ("add_top","add_bottom"):
        return {"kind":"add", "from":"top" if kind=="add_top" else "bottom", "n":1}
    if kind == "mill_take":
        m = re.search(r"\bPut the top (\w+) cards of the Tower into Sheol\b", t, re.I)
        m2 = re.search(r"\badd (?:up to )?(\w+) of those cards\b", t, re.I)
        return {"kind":"mill_take", "mill":n(m.group(1),1) if m else 1, "take":n(m2.group(1),1) if m2 else 1}
    if kind in ("reveal_take","reveal_test"):
        # FIRE reveals into Sheol; every other reveal core takes the card to hand
        to = "sheol" if re.search(r"put that revealed card into Sheol", t, re.I) else "hand"
        return {"kind":"reveal_take" if kind=="reveal_take" else "reveal_test", "n":1, "to":to}
    if kind == "reset_tower":  return {"kind":"reset_tower"}
    if kind == "activate_sheol": return {"kind":"activate_sheol", "where":"sheol"}
    if kind == "exchange_player": return {"kind":"exchange_player", "n":1}
    if kind == "scale_structure": return {"kind":"scale_structure"}
    if kind == "wait_and_activate":
        return {"kind":"wait", "zone":"in_front_of_you"}
    return {"kind":kind} if kind else None

def kicker_of(t: str, kind: str):
    if kind is None: return None
    if kind in ("rest_top","rest_bottom","rest_sheol"):
        return {"kind":"rest", "to":{"rest_top":"tower_top","rest_bottom":"tower_bottom","rest_sheol":"sheol"}[kind],
                "ordered": bool(re.search(r"in any order", t, re.I))}
    if kind == "reorder": return {"kind":"rest", "to":"tower_top", "ordered":True}
    if kind == "draw_one_more": return {"kind":"draw", "n":1}
    if kind == "shuffle": return {"kind":"shuffle", "zone":"tower"}
    if kind == "name_type": return {"kind":"name_type"}
    if kind == "peek": return {"kind":"peek", "n":1, "from":"top"}
    if kind == "reveal_next": return {"kind":"reveal", "n":1, "from":"top"}
    if kind in ("bury_looked","bury_hand"):
        return {"kind":"bury", "n":1, "from":"looked" if kind=="bury_looked" else "hand",
                "to":"tower_bottom", "optional":bool(re.search(r"you may put", t, re.I))}
    return {"kind":kind}

def condition_of(t: str, kind: str):
    if kind is None: return None
    if kind == "stat_threshold":
        m = re.search(r"\btotal ([A-Z]+) ([\w-]+) or more\b", t)
        return {"kind":"pages_stat_total", "stat":m.group(1) if m else None,
                "min":n(m.group(2)) if m else None, "scope":"one_page"}
    if kind == "stat_condition":
        m = re.search(r"\bIf that revealed card has ([A-Z]+) (\w+) or more\b", t)
        return {"kind":"revealed_stat", "stat":m.group(1) if m else None, "min":n(m.group(2)) if m else None,
                "otherwise": bool(re.search(r"otherwise", t, re.I))}
    if kind == "revealed_is_type":
        # FOREIGN tests against the type the player just NAMED, not a fixed one
        if re.search(r"\bis not the named type\b", t, re.I):
            return {"kind":"revealed_named_type", "negated":True}
        if re.search(r"\bis the named type\b", t, re.I):
            return {"kind":"revealed_named_type", "negated":False}
        m = re.search(r"\bIf that revealed card is an? (NOUN|VERB|ADJECTIVE|NAME|TITLE)\b", t)
        return {"kind":"revealed_type", "type":m.group(1) if m else None}
    if kind == "revealed_in_lot": return {"kind":"revealed_in_lot"}
    if kind == "for_each":
        m = re.search(r"\bfor each ([^.;]+)", t, re.I)
        return {"kind":"for_each", "over":m.group(1).strip() if m else None}
    if kind == "if":
        # the classifier's generic fallback; these three are all real, specific tests
        m = re.search(r"\b[Ii]f your revealed card has the higher ([A-Z]+)\b", t)
        if m: return {"kind":"duel_stat", "stat":m.group(1)}
        m = re.search(r"\b[Ii]f that drawn card is an? (NOUN|VERB|ADJECTIVE|NAME|TITLE)\b", t)
        if m: return {"kind":"drawn_type", "type":m.group(1)}
        return {"kind":"if_unparsed"}
    return {"kind":kind}

def interact_of(t: str, kind: str):
    if kind is None: return None
    if kind == "reveal_hand": return {"kind":"reveal_hand", "who":"chosen", "n":1}
    if kind == "lose_card":
        m = re.search(r"\bputs (\w+) cards? from that player's hand\b", t, re.I)
        return {"kind":"lose_card", "who":"chosen", "n":n(m.group(1),1) if m else 1,
                "to":"tower_bottom" if re.search(r"on the bottom of the Tower", t, re.I) else "sheol"}
    if kind == "lose_letter": return {"kind":"lose_letter", "who":"chosen", "n":1}
    if kind == "every_reveals": return {"kind":"reveal_hand", "who":"each", "n":1}
    if kind == "every_material":
        m = re.search(r"\beach player (?:puts|draws|discards) (every|\w+) cards?\b", t, re.I)
        return {"kind":"each_player", "n":"all" if (m and m.group(1).lower()=="every") else n(m.group(1),1) if m else 1}
    if kind == "stat_duel":
        m = re.search(r"\bhigher ([A-Z]+)\b", t)
        return {"kind":"stat_duel", "stat":m.group(1) if m else None}
    if kind == "read_page": return {"kind":"read_page"}
    return {"kind":kind}

def persistent_of(t: str):
    if not re.search(r"\bPut this card in front of you\b", t, re.I): return None
    return {"trigger":{"event":"record_page","scope":"any_player"},
            "effect":{"kind":"activate_in_place","target":"card_in_that_page",
                      "optional":bool(re.search(r"you may", t, re.I)), "stays":True},
            "ends":"on_trigger"}

def spec_for(content: dict) -> dict:
    t = content["ABILITY_TEXT"]; c = ag.classify(t)
    s = {"number": int(content["NUMBER"]), "word": content["WORD"],
         "type": content["CARD_TYPE"], "rarity": content["RARITY_TEXT"],
         "stats": {"lore": int(content["STAT_LORE"]), "context": int(content["STAT_CONTEXT"]),
                   "complexity": int(content["STAT_COMPLEXITY"])},
         "printed_cost": {"COMMON":0,"UNCOMMON":0,"RARE":1,"GLORIOUS":2}[content["RARITY_TEXT"]],
         "cost": cost_of(t), "core": core_of(t, c["core"]), "filter": filter_of(t),
         "kicker": kicker_of(t, c["kicker"]), "condition": condition_of(t, c["condition"]),
         "interact": interact_of(t, c["interact"]), "persistent": persistent_of(t),
         "timing": {"kind": c["timing"]}, "text": t}
    # KINGDOM hands every player a new Lot; nothing in the 7-slot vector carries it.
    if re.search(r"exchanges that player's Lot for a new one", t, re.I):
        s["interact"] = {"kind": "exchange_lots", "who": "each"}
    s = {k: v for k, v in s.items() if v is not None}
    s = attach_branches(s, t)
    # The execution plan the game actually runs: effects in printed order. The
    # slot vector above stays for the design gates, which classify shapes.
    s["effects"] = FX.apply_scaling(FX.effects_of(t), t)
    s = mark_cost(s)
    return s


# A CONDITION with no consequent does nothing. Nine cards in the set print
# "if <test>, <reward>" and the reward has to survive extraction, so parse the
# clause after the test into an effect of its own.
def _clause_effect(clause: str):
    if not clause: return None
    clause = clause.split(".")[0]
    m = re.search(r"\bgain (\w+) Letters?\b", clause, re.I)
    if m: return {"kind":"gain_letter", "n":n(m.group(1),1)}
    m = re.search(r"\bdraw (\w+) cards? from the Tower\b", clause, re.I)
    if m: return {"kind":"draw", "n":n(m.group(1),1)}
    m = re.search(r"\badd (up to )?(\w+) cards? from Sheol to your hand\b", clause, re.I)
    if m: return {"kind":"recover", "n":n(m.group(2),1), "up_to": bool(m.group(1))}
    return None


def _branches(t: str):
    """The 'then' and 'otherwise' clauses of a printed conditional."""
    m = re.search(r"\b[Ii]f\b(.*)$", t, re.S)
    if not m: return None, None
    rest = m.group(1)
    i = rest.find(",")
    if i < 0: return None, None
    parts = re.split(r";\s*otherwise,?\s*", rest[i+1:], maxsplit=1, flags=re.I)
    return parts[0], (parts[1] if len(parts) > 1 else None)


def _same(a, b) -> bool:
    return bool(a) and bool(b) and all(b.get(k) == v for k, v in a.items())


# A COST is not an effect: "costs are paid before effects", and an ability whose
# cost cannot be paid does not happen. ADAM discards one of your Pages before it
# rebuilds the Tower and draws four - with no Page, it should do nothing at all,
# and instead it was skipping the price and keeping the goods.
#
# In the printed grammar a cost is the first clause and it takes something of
# yours away, so that is exactly what gets marked.
COST_KINDS = ("discard", "bury", "discard_page", "spend_letter")


def mark_cost(spec: dict) -> dict:
    effects = spec.get("effects") or []
    if not effects:
        return spec
    first = effects[0]
    if first.get("kind") in COST_KINDS and first.get("from", "hand") == "hand":
        first["cost"] = True
    return spec


def attach_branches(spec: dict, t: str) -> dict:
    """Give the CONDITION its consequent, or mark that it gates the CORE."""
    cond = spec.get("condition")
    if not cond: return spec
    met, otherwise = _branches(t)
    core, kicker = spec.get("core"), spec.get("kicker")
    e_met, e_not = _clause_effect(met), _clause_effect(otherwise)
    if e_met:
        if _same(e_met, core):     cond["gates"], cond["gates_when"] = "core", "met"
        elif _same(e_met, kicker): cond["gates"], cond["gates_when"] = "kicker", "met"
        else:                      cond["when_met"] = e_met
    if e_not:
        # CONFUSE: the CORE is the *otherwise* branch, not the reward
        if _same(e_not, core): cond["gates"], cond["gates_when"] = "core", "not"
        else:                  cond["when_not"] = e_not
    return spec


def lua(v, indent=2):
    pad = " " * indent
    if isinstance(v, dict):
        inner = ",\n".join(f"{pad}  {k} = {lua(x, indent+2)}" for k, x in v.items())
        return "{\n" + inner + f"\n{pad}}}"
    if isinstance(v, list):
        return "{ " + ", ".join(lua(x, indent) for x in v) + " }"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, (int, float)): return str(v)
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'

def main(out: Path):
    specs = []
    for p in sorted(SERIES.glob("cards/*/card.json")):
        specs.append(spec_for(json.loads(p.read_text(encoding="utf-8"))["content"]))
    lines = ["-- GENERATED by scripts/pipeline/export_specs.py in the Hypertext repo.",
             "-- Do not edit by hand: the printed card is upstream of this file.",
             "return {"]
    for s in specs:
        lines.append(f"  [{s['number']}] = " + lua(s) + ",")
    lines.append("}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(specs)} specs -> {out}")
    return specs
def export_lots(out: Path):
    """Lot recipes, structure intact.

    The first export flattened every recipe to a list of card types, which
    silently destroyed the seven Lots whose recipes are *counted groups*
    ("4 of one type + 1 any") rather than fixed types - they could never be
    matched. templates/phases.yml is upstream; keep recipe.kind.
    """
    import yaml
    doc = yaml.safe_load((ROOT / "templates" / "phases.yml").read_text(encoding="utf-8"))
    sizes = {5: (8, 2, 1), 6: (10, 2, 1), 7: (14, 3, 2)}
    lots = []
    for ph in doc["phases"]:
        cv, owner, visitor = sizes[ph["cards"]]
        lots.append({"id": ph["id"], "name": ph["name"], "cards": ph["cards"],
                     "recipe": ph["recipe"], "display": ph["display"],
                     "chapter_value": cv, "owner_letters": owner, "visitor_letters": visitor})
    lines = ["-- GENERATED by scripts/pipeline/export_specs.py in the Hypertext repo.",
             "-- Do not edit by hand: templates/phases.yml is upstream of this file.",
             "return {"]
    for l in lots:
        lines.append(f"  [{l['id']}] = " + lua(l) + ",")
    lines.append("}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(lots)} lots -> {out}")
    return lots


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "lots":
        export_lots(Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/lots.lua"))
    else:
        main(Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/cards.lua"))
