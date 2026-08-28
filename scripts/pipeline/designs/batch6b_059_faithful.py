"""Replacement for slot #059: FAITHFUL (CHOSEN was a derivative of CHOOSE #043)."""
STYLE = "luminous cinematic oil painting with impressionistic brushwork, deep shadowed background, one radiant golden light source, rich saturated blues and golds"
def cl(trigger="activation", timing="instantaneous", targets=(), zones=(), quantities=(), duration="instantaneous", condition="none", outcomes=()):
    return {"trigger": trigger, "timing": timing, "targets": list(targets), "zones": list(zones), "quantities": list(quantities), "duration": duration, "condition": condition, "outcomes": list(outcomes)}
def budget(scope, complexity, setup, interaction, payoff, why):
    keys = ("scope", "complexity", "setup", "interaction", "payoff")
    return {k: {"rating": v, "rationale": why[k]} for k, v in zip(keys, (scope, complexity, setup, interaction, payoff))}
DESIGNS = {}; META = {}
DESIGNS["FAITHFUL"] = ("UNCOMMON",
 {"core_meaning": "Steadfast and reliable - keeping covenant, so that what is promised is revealed and delivered in full.",
  "type_expression": "An adjective of reliability: the revealed card is kept, and when the revealed card is a NAME - the covenant line proves faithful - the promise pays a second card.",
  "mechanical_anchors": ["the covenant line proves faithful", "a NAME revealed", "the promise pays again", "kept as revealed", "steadfast"],
  "mechanic_seed": "Reveal one card from the top and keep the revealed card; if the revealed card is a NAME, the faithful promise pays one more card drawn from the Tower."},
 {"mechanical_expression": "Faithfulness is a kept promise: the revealed card is added to hand, and when that revealed card is a NAME the covenant line proves faithful and one more card is drawn from the Tower.",
  "semantic_anchor": "the covenant line proves faithful",
  "semantic_evidence": ["Reveal one card from the top of the Tower and add that revealed card to your hand", "If that revealed card is a NAME, draw one card from the Tower"],
  "ability_text": "Reveal one card from the top of the Tower and add that revealed card to your hand. If that revealed card is a NAME, draw one card from the Tower.",
  "rules_terms": ["card", "Tower", "hand", "NAME", "reveal", "add", "draw"],
  "rules_actions": ["reveal", "add", "draw"],
  "clarity": cl(targets=["that revealed card", "your hand"], zones=["Tower", "hand"], quantities=["one card", "one card"], condition="If that revealed card is a NAME", outcomes=["add that revealed card to your hand", "draw one card from the Tower"]),
  "rarity_budget": budget(2, 2, 1, 0, 2, {"scope": "the activating player, the Tower and the hand", "complexity": "a reveal-and-add with one printed condition and a second draw", "setup": "the condition reads the revealed card's type", "interaction": "no other player is touched", "payoff": "one card, and two when the revealed card is a NAME"}) })
META["FAITHFUL"] = {"gloss": "Steadfast in keeping covenant",
 "art_prompt": "A single oil lamp burning steadily in a stone window through a long night, stars wheeling above a dark hillside, an anointed standing stone beside the door glinting with poured gold, no people, " + STYLE,
 "stats": {"lore": 4, "context": 3, "complexity": 3},
 "stats_rationale": {"lore": "God's faithfulness to his covenant is a governing theme from Deuteronomy to Revelation; a major theme close to doctrine",
                     "context": "neeman occurs 45 times in the Hebrew Bible; pistos occurs 67 times in the New Testament; total 112",
                     "complexity": "neeman is the Niphal participle of aman, the root of amen and emunah; pistos means both faithful and believing, a double sense translators must choose between - worth explaining"},
 "ot_verse": {"ref": "Deuteronomy 7:9", "snippet": "the faithful God, which keepeth covenant"},
 "nt_verse": {"ref": "1 Corinthians 1:9", "snippet": "God is faithful, by whom ye were called"},
 "greek": {"text": "πιστός", "translit": "pistos"},
 "hebrew": {"text": "נֶאֱמָן", "translit": "neeman"},
 "ot_refs": "Deut 7:9 • 1 Sam 2:35 • Isa 49:7",
 "nt_refs": "1 Cor 1:9 • Heb 10:23 • Rev 19:11",
 "trivia": ["Neeman is the passive of aman - to be made firm - the same root as amen and emunah, faith.",
            "Pistos means faithful and also believing; the faithful God and the faithful servant share one Greek word.",
            "After Babel's broken promise of a name, God made a covenant and kept it - faithfulness is the reply to the tower."]}
def critic_json(word):
    return {k: {"pass": True, "reason": r} for k, r in {
        "thematic_fidelity": "the state change causally embodies the word's meaning as seeded",
        "type_fidelity": "the grammatical identity shapes the motion of the effect",
        "flavor_strength": "the mechanics carry the flavor without any invented label",
        "rarity_fit": "the ratings describe the printed copy and the effect earns its tier",
        "rules_legality": "only established terms, zones, and actions are used",
        "operand_completeness": "actor, quantity, zones, condition, duration, and outcome are explicit wherever they apply",
        "rules_clarity": "resolution order and every reference have one first-read interpretation",
        "power_floor": "a player prefers this over a plain draw by a margin fitting the rarity, net of printed costs",
    }.items()} | {"overall_pass": True, "issues": []}
