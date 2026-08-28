"""Batch 5 designs: slots #052-#056 (HOVER, NEW, DESTROYER, SHEPHERD, ASCEND)."""
STYLE = "luminous cinematic oil painting with impressionistic brushwork, deep shadowed background, one radiant golden light source, rich saturated blues and golds"

def cl(trigger="activation", timing="instantaneous", targets=(), zones=(), quantities=(), duration="instantaneous", condition="none", outcomes=()):
    return {"trigger": trigger, "timing": timing, "targets": list(targets), "zones": list(zones), "quantities": list(quantities), "duration": duration, "condition": condition, "outcomes": list(outcomes)}

def budget(scope, complexity, setup, interaction, payoff, why):
    keys = ("scope", "complexity", "setup", "interaction", "payoff")
    return {k: {"rating": v, "rationale": why[k]} for k, v in zip(keys, (scope, complexity, setup, interaction, payoff))}

DESIGNS = {}
META = {}

# ---------------------------------------------------------------- #052 HOVER
DESIGNS["HOVER"] = ("GLORIOUS",
 {"core_meaning": "To brood in suspended motion above the deep, the way the Spirit hovered over the formless waters before anything was drawn forth.",
  "type_expression": "A verb of sustained, sheltering motion: every player at the table feels the brooding breath, and then the activating player chooses what rises out of the deep.",
  "mechanical_anchors": ["over the deep", "brooding breath", "rises from Sheol", "every player breathes", "up to three from the deep"],
  "mechanic_seed": "Hover over the deep of Sheol: each player draws one breath of life from the Tower, then the hovering one chooses up to three cards that lie in the deep and lifts those chosen cards into the hand."},
 {"mechanical_expression": "The hovering Spirit gives breath to the whole table first - each player draws one card - and then what lay formless in the deep rises from Sheol: the activating player chooses up to three cards in Sheol and adds those chosen cards to hand.",
  "semantic_anchor": "rises from Sheol",
  "semantic_evidence": ["Each player draws one card from the Tower", "choose up to three cards in Sheol and add those chosen cards to your hand"],
  "ability_text": "Each player draws one card from the Tower. Then choose up to three cards in Sheol and add those chosen cards to your hand.",
  "rules_terms": ["player", "card", "cards", "Tower", "Sheol", "hand", "draw", "choose", "add"],
  "rules_actions": ["draw", "choose", "add"],
  "clarity": cl(targets=["Each player", "your hand"], zones=["Tower", "Sheol", "hand"], quantities=["one card", "up to three cards"], outcomes=["Each player draws one card from the Tower", "add those chosen cards to your hand"]),
  "rarity_budget": budget(3, 3, 1, 3, 3, {"scope": "touches every player and three zones - Tower, Sheol, hand", "complexity": "a table-wide draw followed by a scaling selective recovery", "setup": "reads Sheol, which fills as the Chapter proceeds", "interaction": "every player draws a card", "payoff": "the activating player gains one draw plus up to three cards from Sheol - four cards against two discards paid"}) })
META["HOVER"] = {"gloss": "To brood over the face of the waters",
 "art_prompt": "A vast black ocean beneath a starless void, a radiant golden light spreading low over the still waters like outstretched wings of mist, ripples of luminous blue awakening beneath the glow, deep shadow all around, " + STYLE,
 "stats": {"lore": 5, "context": 1, "complexity": 4},
 "stats_rationale": {"lore": "Genesis 1:2 - the Spirit of God brooding over the deep is the first act of the Spirit in Scripture and the seed of every doctrine of the Spirit's creative work; a doctrine hangs on this verse",
                     "context": "rachaph occurs 3 times in the Hebrew Bible (Gen 1:2, Deut 32:11, Jer 23:9); epiphero occurs 3 times in the New Testament (Rom 3:5, Phil 1:16, Jude 1:9); total 6",
                     "complexity": "rachaph is rare and its sense is disputed - brood, hover, or shake (Jer 23:9); Syriac and Ugaritic cognates mean to brood like a bird; the Septuagint rendered it epiphero, to bring upon, which the New Testament uses of God bringing wrath"},
 "ot_verse": {"ref": "Genesis 1:2", "snippet": "the Spirit of God moved upon the face of the waters"},
 "nt_verse": {"ref": "Romans 3:5", "snippet": "Is God unrighteous who taketh vengeance?"},
 "greek": {"text": "ἐπιφέρω", "translit": "epiphero"},
 "hebrew": {"text": "רָחַף", "translit": "rachaph"},
 "ot_refs": "Gen 1:2 • Deut 32:11 • Jer 23:9",
 "nt_refs": "Rom 3:5 • Phil 1:16 • Jude 1:9",
 "trivia": ["Rachaph appears only three times; in Deuteronomy 32 it is the eagle fluttering over her young, so many read Genesis 1:2 as the Spirit brooding like a bird.",
            "The Septuagint rendered it epiphero, to bring upon, the same verb Paul uses of God bringing wrath - creation and judgment share one word.",
            "Before Babel's builders reached upward, the Spirit had already come down to hover over an empty deep."]}

# ------------------------------------------------------------------ #053 NEW
DESIGNS["NEW"] = ("COMMON",
 {"core_meaning": "Fresh in kind rather than merely recent - a new tongue, a new heart, a new people unlike what was there before.",
  "type_expression": "An adjective of novelty: the card just drawn is judged by whether its kind is unheard in the hand, and a fresh kind is rewarded.",
  "mechanical_anchors": ["a kind unheard in the hand", "fresh tongue", "new to the hand", "reward the novel", "no other card shares"],
  "mechanic_seed": "Draw one card and test its novelty: if no other card in the hand shares that drawn card's type, the new tongue earns one Letter."},
 {"mechanical_expression": "Novelty is measured against the hand: the drawn card is new to the hand when no other card there shares its card type, and only then does the new tongue earn a Letter.",
  "semantic_anchor": "new to the hand",
  "semantic_evidence": ["Draw one card from the Tower", "no other card in your hand shares that drawn card's card type"],
  "ability_text": "Draw one card from the Tower. If no other card in your hand shares that drawn card's card type, gain one Letter.",
  "rules_terms": ["card", "Tower", "hand", "card type", "Letter", "draw", "gain"],
  "rules_actions": ["draw", "gain"],
  "clarity": cl(targets=["your hand", "that drawn card"], zones=["Tower", "hand"], quantities=["one card", "one Letter"], condition="If no other card in your hand shares that drawn card's card type", outcomes=["Draw one card from the Tower", "gain one Letter"]),
  "rarity_budget": budget(1, 2, 0, 0, 1, {"scope": "the activating player, the Tower and the hand", "complexity": "one draw with one printed condition", "setup": "no prior state is required; the condition reads the hand as it stands", "interaction": "no other player is touched", "payoff": "one card, with a Letter only when the drawn kind is new to the hand"}) })
META["NEW"] = {"gloss": "A new tongue, a new heart, a new people",
 "art_prompt": "An upper room at dawn seen from behind a gathered crowd, small tongues of golden flame hovering above bowed heads, a rushing wind stirring robes, one radiant light breaking through the open door into deep shadow, " + STYLE,
 "stats": {"lore": 4, "context": 3, "complexity": 3},
 "stats_rationale": {"lore": "new covenant, new heart, new creation, new tongues - the reversal of Babel at Pentecost and the new-creation theme run through this word; a recognized theme close to doctrine",
                     "context": "chadash occurs 53 times in the Hebrew Bible; kainos occurs 42 times in the New Testament; total 95",
                     "complexity": "Greek keeps two words, kainos (new in kind) and neos (new in time), and chadash covers both; the choice of kainos for the new covenant and new tongues is a translation decision worth explaining"},
 "ot_verse": {"ref": "Ezekiel 36:26", "snippet": "A new heart also will I give you, and a new spirit"},
 "nt_verse": {"ref": "Mark 16:17", "snippet": "they shall speak with new tongues"},
 "greek": {"text": "καινός", "translit": "kainos"},
 "hebrew": {"text": "חָדָשׁ", "translit": "chadash"},
 "ot_refs": "Ezek 36:26 • Isa 65:17 • Lam 3:23",
 "nt_refs": "Mark 16:17 • 2 Cor 5:17 • Rev 21:5",
 "trivia": ["Greek has two words for new: neos means recent, kainos means unprecedented in kind; the new tongues and the new covenant are kainos.",
            "Babel confused one tongue into many; at Pentecost many tongues carried one message - a new thing, not a repaired old one.",
            "Chadash also names the new moon, chodesh - the month begins when the light is made new."]}

# ------------------------------------------------------------ #054 DESTROYER
DESIGNS["DESTROYER"] = ("UNCOMMON",
 {"core_meaning": "The agent of God's wrath who passes through at midnight and strikes one household while the watchful are spared.",
  "type_expression": "A title of office: the destroyer is sent against one chosen household, and the judgment on another player becomes the activating player's gain.",
  "mechanical_anchors": ["strikes one household", "sent against another player", "midnight judgment", "the marked are spared", "one card into Sheol"],
  "mechanic_seed": "Send the destroyer against one chosen household: that chosen player loses one card from hand into Sheol, and the one who sent judgment draws one card."},
 {"mechanical_expression": "The destroyer is sent against another player: the chosen player's household loses one card from hand into Sheol, and the activating player who sent the judgment draws one card from the Tower.",
  "semantic_anchor": "sent against another player",
  "semantic_evidence": ["Choose another player", "That chosen player puts one card from that chosen player's hand into Sheol"],
  "ability_text": "Choose another player. That chosen player puts one card from that chosen player's hand into Sheol; then draw one card from the Tower.",
  "rules_terms": ["player", "card", "hand", "Sheol", "Tower", "choose", "put", "draw"],
  "rules_actions": ["choose", "put", "draw"],
  "clarity": cl(targets=["another player", "That chosen player"], zones=["hand", "Sheol", "Tower"], quantities=["one card"], outcomes=["puts one card from that chosen player's hand into Sheol", "draw one card from the Tower"]),
  "rarity_budget": budget(2, 2, 1, 1, 1, {"scope": "another player and three zones - hand, Sheol, Tower", "complexity": "one forced discard and one draw", "setup": "the chosen player must hold a card", "interaction": "one chosen player loses one card", "payoff": "one card drawn, with the opponent one card poorer"}) })
META["DESTROYER"] = {"gloss": "The agent of God's wrath sent through the land",
 "art_prompt": "A moonlit Egyptian street at midnight, a towering shadow sweeping past a doorway whose lintel glows red-gold in lamplight, palm silhouettes and deep indigo darkness beyond, one radiant golden light within the door, " + STYLE,
 "stats": {"lore": 3, "context": 2, "complexity": 4},
 "stats_rationale": {"lore": "the Passover destroyer and the plague of 1 Corinthians 10 carry the theme of judgment passing over the marked; a recognized theme rather than a doctrine",
                     "context": "mashchit occurs 19 times in the Hebrew Bible; olothreutes occurs 1 time in the New Testament (1 Cor 10:10); total 20",
                     "complexity": "mashchit is the Hiphil participle of shachath, to ruin or corrupt, and also means the pit; the Septuagint's olethreuon in Exodus 12 becomes Paul's olothreutes, a New Testament hapax, and Revelation names the same office Apollyon"},
 "ot_verse": {"ref": "Exodus 12:23", "snippet": "will not suffer the destroyer to come in unto your houses"},
 "nt_verse": {"ref": "1 Corinthians 10:10", "snippet": "and were destroyed of the destroyer"},
 "greek": {"text": "ὀλοθρευτής", "translit": "olothreutes"},
 "hebrew": {"text": "מַשְׁחִית", "translit": "mashchit"},
 "ot_refs": "Exod 12:23 • 2 Sam 24:16 • Jer 51:25",
 "nt_refs": "1 Cor 10:10",
 "trivia": ["Mashchit is a participle - the one ruining - and the same word names the pit of corruption in Psalm 55.",
            "Paul's olothreutes in 1 Corinthians 10 is a New Testament hapax, echoing the Septuagint's word for the Passover destroyer.",
            "Revelation gives the office a name in two tongues, Abaddon and Apollyon - the Destroyer."]}

# ------------------------------------------------------------- #055 SHEPHERD
DESIGNS["SHEPHERD"] = ("COMMON",
 {"core_meaning": "The one who gathers scattered sheep into one fold, letting a stray go only to bring another in.",
  "type_expression": "A title of office: the shepherd gathers steadily, one sheep at a time, and may release one stray to bring another into the fold.",
  "mechanical_anchors": ["gathers one at a time", "release a stray", "into the fold", "bring another in", "one sheep from the Tower"],
  "mechanic_seed": "Gather one sheep from the Tower, then release one stray from the hand into Sheol to gather another sheep from the Tower."},
 {"mechanical_expression": "The shepherd gathers one card from the Tower, and may release a stray - discard one card from hand - to bring another in: when a card is discarded, one more card is drawn from the Tower.",
  "semantic_anchor": "release a stray",
  "semantic_evidence": ["Draw one card from the Tower", "you may discard one card from your hand", "if you discard one card from your hand, draw another card from the Tower"],
  "ability_text": "Draw one card from the Tower. Then you may discard one card from your hand; if you discard one card from your hand, draw another card from the Tower.",
  "rules_terms": ["card", "Tower", "hand", "draw", "discard"],
  "rules_actions": ["draw", "discard", "draw"],
  "clarity": cl(targets=["your hand"], zones=["Tower", "hand"], quantities=["one card", "another card"], condition="if you discard one card from your hand", outcomes=["Draw one card from the Tower", "draw another card from the Tower"]),
  "rarity_budget": budget(1, 2, 0, 0, 1, {"scope": "the activating player, the Tower and the hand", "complexity": "a draw with one optional discard-and-draw", "setup": "no prior state is required", "interaction": "no other player is touched", "payoff": "one card, plus a card-neutral cycle of one stray"}) })
META["SHEPHERD"] = {"gloss": "The one who gathers his scattered sheep",
 "art_prompt": "A lone shepherd seen from behind on a dusk hillside, staff raised, guiding scattered sheep down toward a stone fold whose gate glows with one radiant golden lantern, deep blue shadowed valley beyond, " + STYLE,
 "stats": {"lore": 4, "context": 3, "complexity": 2},
 "stats_rationale": {"lore": "the LORD is my shepherd and I am the good shepherd - the shepherd is a governing image of God's care and of Christ, a major theme close to doctrine",
                     "context": "roeh as the noun shepherd occurs 62 times in the Hebrew Bible; poimen occurs 18 times in the New Testament; total 80",
                     "complexity": "roeh is the participle of raah, to pasture or feed, so shepherd and feeder are one word; poimen is straightforward and gives us pastor by way of Latin"},
 "ot_verse": {"ref": "Psalm 23:1", "snippet": "The LORD is my shepherd; I shall not want"},
 "nt_verse": {"ref": "John 10:11", "snippet": "I am the good shepherd"},
 "greek": {"text": "ποιμήν", "translit": "poimen"},
 "hebrew": {"text": "רֹעֶה", "translit": "roeh"},
 "ot_refs": "Ps 23:1 • Isa 40:11 • Ezek 34:23",
 "nt_refs": "John 10:11 • Heb 13:20 • 1 Pet 2:25",
 "trivia": ["Roeh means the one who pastures - the shepherd is literally the feeder of the flock.",
            "Ezekiel 34 promises one shepherd over the scattered; John 10 answers with one fold and one shepherd.",
            "Pastor is simply the Latin for shepherd; the office kept the old name."]}

# --------------------------------------------------------------- #056 ASCEND
DESIGNS["ASCEND"] = ("UNCOMMON",
 {"core_meaning": "To climb upward toward heaven by human strength, reaching for the heights that only descend as a gift.",
  "type_expression": "A verb of climbing: the player scales the top of the Tower, sets the rungs in order, and is rewarded only when the reach truly attains the heights.",
  "mechanical_anchors": ["climb the top of the Tower", "set the rungs in order", "reach the heights", "a Letter for the summit", "LORE four or more"],
  "mechanic_seed": "Climb: look at the top four cards of the Tower and set those rungs back in any order, then draw the next card; a drawn card with LORE four or more is the summit and earns one Letter."},
 {"mechanical_expression": "The climber scales the top of the Tower - looks at the top four cards and puts those rungs back in any order - then draws; when the drawn card has LORE four or more the climb has managed to reach the heights, and one Letter is gained for the summit.",
  "semantic_anchor": "reach the heights",
  "semantic_evidence": ["Look at the top four cards of the Tower", "put those cards back on top of the Tower in any order", "if that drawn card has LORE four or more, gain one Letter"],
  "ability_text": "Look at the top four cards of the Tower and put those cards back on top of the Tower in any order. Then draw one card from the Tower; if that drawn card has LORE four or more, gain one Letter.",
  "rules_terms": ["cards", "card", "Tower", "LORE", "Letter", "look at", "put", "draw", "gain"],
  "rules_actions": ["look at", "put", "draw", "gain"],
  "clarity": cl(targets=["the top four cards of the Tower", "that drawn card"], zones=["Tower"], quantities=["top four cards", "one card", "one Letter"], condition="if that drawn card has LORE four or more", outcomes=["put those cards back on top of the Tower in any order", "draw one card from the Tower", "gain one Letter"]),
  "rarity_budget": budget(1, 2, 1, 0, 2, {"scope": "the activating player and the Tower", "complexity": "a look-and-reorder, a draw, and one printed condition", "setup": "the condition reads the drawn card's LORE", "interaction": "no other player is touched", "payoff": "one chosen draw from a stacked top, plus a Letter when the summit is reached"}) })
META["ASCEND"] = {"gloss": "To climb toward heaven in human strength",
 "art_prompt": "A colossal brick ziggurat spiraling up into storm clouds, tiny figures climbing its ramps seen from far below, a break of radiant golden light at the summit against deep indigo sky, " + STYLE,
 "stats": {"lore": 4, "context": 5, "complexity": 3},
 "stats_rationale": {"lore": "no man hath ascended up to heaven but he that came down - the ascension and the futility of climbing to God by strength are doctrine-bearing themes, though the verb itself is ordinary",
                     "context": "alah occurs 890 times in the Hebrew Bible; anabaino occurs 82 times in the New Testament; total 972",
                     "complexity": "alah underlies olah, the burnt offering that goes up, and the modern aliyah; anabaino gives the ascension its name - a derivation worth explaining"},
 "ot_verse": {"ref": "Isaiah 14:13", "snippet": "thou hast said in thine heart, I will ascend into heaven"},
 "nt_verse": {"ref": "John 3:13", "snippet": "no man hath ascended up to heaven, but he that came down"},
 "greek": {"text": "ἀναβαίνω", "translit": "anabaino"},
 "hebrew": {"text": "עָלָה", "translit": "alah"},
 "ot_refs": "Isa 14:13 • Ps 24:3 • Gen 28:12",
 "nt_refs": "John 3:13 • Eph 4:8 • Rom 10:6",
 "trivia": ["The burnt offering is the olah, the going-up, from the same verb - sacrifice ascends where the builders could not.",
            "The king of Babylon boasts I will ascend into heaven in Isaiah 14, the tower's ambition in one sentence.",
            "Jacob's ladder shows angels ascending and descending; John 1:51 says they do so upon the Son of man."]}

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

# ---- overrides after offline validation (printed ratings must sit inside the rarity range) ----
META["HOVER"]["stats_rationale"]["context"] = "rachaph occurs 3 times in the Hebrew Bible; epiphero occurs 3 times in the New Testament; total 6"

DESIGNS["NEW"] = ("COMMON",
 {"core_meaning": "Fresh in kind rather than merely recent - a new tongue, a new heart, a new people replacing what was there before.",
  "type_expression": "An adjective of renewal: the card revealed from the top of the Tower is the new thing, and an old card of the same kind may be sent to the bottom to make room for the new.",
  "mechanical_anchors": ["the new replaces the old", "same kind sent to the bottom", "revealed from the top", "make room for the new", "a fresh tongue in hand"],
  "mechanic_seed": "Reveal the top card and take the new thing into hand; then the old card of the same kind may go to the bottom of the Tower, the new replacing the old."},
 {"mechanical_expression": "Renewal is a replacement: the card revealed from the top of the Tower is the new thing added to hand, and one old card of the same kind may be sent to the bottom of the Tower so that the new replaces the old.",
  "semantic_anchor": "the new replaces the old",
  "semantic_evidence": ["Reveal the top card of the Tower and add that revealed card to your hand", "put one other card from your hand with the same card type as that revealed card on the bottom of the Tower"],
  "ability_text": "Reveal the top card of the Tower and add that revealed card to your hand. Then you may put one other card from your hand with the same card type as that revealed card on the bottom of the Tower.",
  "rules_terms": ["card", "Tower", "hand", "card type", "reveal", "add", "put"],
  "rules_actions": ["reveal", "add", "put"],
  "clarity": cl(targets=["that revealed card", "your hand"], zones=["Tower", "hand"], quantities=["the top card", "one other card"], outcomes=["add that revealed card to your hand", "put one other card from your hand with the same card type as that revealed card on the bottom of the Tower"]),
  "rarity_budget": budget(2, 2, 0, 0, 1, {"scope": "the activating player, the Tower and the hand", "complexity": "a reveal-and-add with one optional placement", "setup": "no prior state is required", "interaction": "no other player is touched", "payoff": "one card, with an optional swap of an old card of the same kind"}) })

DESIGNS["SHEPHERD"] = ("COMMON",
 {"core_meaning": "The one who gathers scattered sheep, taking one into the fold and setting the rest of the flock in order.",
  "type_expression": "A title of office: the shepherd looks over the top of the flock, gathers one into hand, and leaves the other sheep in the order the shepherd chooses.",
  "mechanical_anchors": ["gathers one into the fold", "sets the flock in order", "looks over the top of the flock", "the other sheep stay", "one sheep from the Tower"],
  "mechanic_seed": "Look over the top three of the flock, gather one into hand, and put the other sheep back on top of the Tower in the order the shepherd chooses."},
 {"mechanical_expression": "The shepherd sets the flock in order: three cards from the top of the Tower are looked over, one is gathered into hand, and the other cards go back on top in the order the shepherd chooses.",
  "semantic_anchor": "sets the flock in order",
  "semantic_evidence": ["Look at the top three cards of the Tower", "put the other cards on top of the Tower in any order"],
  "ability_text": "Look at the top three cards of the Tower. Add one of those cards to your hand and put the other cards on top of the Tower in any order.",
  "rules_terms": ["cards", "Tower", "hand", "look at", "add", "put"],
  "rules_actions": ["look at", "add", "put"],
  "clarity": cl(targets=["the top three cards of the Tower", "your hand"], zones=["Tower", "hand"], quantities=["top three cards", "one of those cards"], outcomes=["Add one of those cards to your hand", "put the other cards on top of the Tower in any order"]),
  "rarity_budget": budget(2, 2, 0, 0, 1, {"scope": "the activating player, the Tower and the hand", "complexity": "a look, one add, and a reorder of the rest", "setup": "no prior state is required", "interaction": "no other player is touched", "payoff": "one chosen card of three, with the other two set in order for the next draws"}) })

DESIGNS["ASCEND"] = ("UNCOMMON",
 {"core_meaning": "To climb upward toward heaven by human strength, reaching for the heights that may or may not be attained.",
  "type_expression": "A verb of climbing: the player scales the top of the Tower and may take only a card of the heights - LORE four or more - leaving the other rungs in chosen order.",
  "mechanical_anchors": ["climb the top of the Tower", "reach the heights", "only the high may be taken", "rungs left in order", "LORE four or more"],
  "mechanic_seed": "Climb: look at the top four cards of the Tower, take up to one card of the heights - LORE four or more - into hand, and leave the other rungs on top in the order the climber chooses."},
 {"mechanical_expression": "The climber scales the top four cards of the Tower and may reach the heights only where a card has LORE four or more - up to one such card is added to hand - while the other rungs are put back on top in the order the climber chooses.",
  "semantic_anchor": "reach the heights",
  "semantic_evidence": ["Look at the top four cards of the Tower", "Add up to one of those cards that has LORE four or more to your hand", "put the other cards on top of the Tower in any order"],
  "ability_text": "Look at the top four cards of the Tower. Add up to one of those cards that has LORE four or more to your hand and put the other cards on top of the Tower in any order.",
  "rules_terms": ["cards", "Tower", "hand", "LORE", "look at", "add", "put"],
  "rules_actions": ["look at", "add", "put"],
  "clarity": cl(targets=["the top four cards of the Tower", "your hand"], zones=["Tower", "hand"], quantities=["top four cards", "up to one of those cards"], outcomes=["Add up to one of those cards that has LORE four or more to your hand", "put the other cards on top of the Tower in any order"]),
  "rarity_budget": budget(2, 2, 0, 0, 1, {"scope": "the activating player, the Tower and the hand", "complexity": "a four-card look with a stat-hooked selection and a reorder", "setup": "no prior state is required", "interaction": "no other player is touched", "payoff": "up to one high-LORE card of four, with the rest set in order"}) })

_new = DESIGNS["NEW"][2]
_new["ability_text"] = "Reveal one card from the top of the Tower and add that revealed card to your hand. Then you may put one other card from your hand with the same card type as that revealed card on the bottom of the Tower."
_new["semantic_evidence"] = ["Reveal one card from the top of the Tower and add that revealed card to your hand", "put one other card from your hand with the same card type as that revealed card on the bottom of the Tower"]
_new["clarity"]["quantities"] = ["one card", "one other card"]
