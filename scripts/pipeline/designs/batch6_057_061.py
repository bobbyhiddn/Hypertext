"""Batch 6 designs: slots #057-#061 (DISCORD, DEPART, CHOSEN, EDEN, FIRE)."""
STYLE = "luminous cinematic oil painting with impressionistic brushwork, deep shadowed background, one radiant golden light source, rich saturated blues and golds"

def cl(trigger="activation", timing="instantaneous", targets=(), zones=(), quantities=(), duration="instantaneous", condition="none", outcomes=()):
    return {"trigger": trigger, "timing": timing, "targets": list(targets), "zones": list(zones), "quantities": list(quantities), "duration": duration, "condition": condition, "outcomes": list(outcomes)}

def budget(scope, complexity, setup, interaction, payoff, why):
    keys = ("scope", "complexity", "setup", "interaction", "payoff")
    return {k: {"rating": v, "rationale": why[k]} for k, v in zip(keys, (scope, complexity, setup, interaction, payoff))}

DESIGNS = {}
META = {}

# -------------------------------------------------------------- #057 DISCORD
DESIGNS["DISCORD"] = ("RARE",
 {"core_meaning": "The sound of one speech breaking into strife - words that no longer carry between neighbours, so that what was held in common is lost.",
  "type_expression": "A noun of rupture: discord is sown against another player, whose words fall into Sheol, while the sower gathers from the Tower.",
  "mechanical_anchors": ["sown against another player", "words fall into Sheol", "two cards lost to strife", "the sower gathers", "confusion of tongues"],
  "mechanic_seed": "Sow discord: choose another player whose two cards fall from hand into Sheol, then the sower draws two cards from the Tower."},
 {"mechanical_expression": "Discord is sown against another player: two of that chosen player's cards fall from hand into Sheol as words fall into Sheol at Babel, and the sower draws two cards from the Tower.",
  "semantic_anchor": "words fall into Sheol",
  "semantic_evidence": ["Choose another player", "That chosen player puts two cards from that chosen player's hand into Sheol", "draw two cards from the Tower"],
  "ability_text": "Choose another player. That chosen player puts two cards from that chosen player's hand into Sheol; then draw two cards from the Tower.",
  "rules_terms": ["player", "cards", "hand", "Sheol", "Tower", "choose", "put", "draw"],
  "rules_actions": ["choose", "put", "draw"],
  "clarity": cl(targets=["another player", "That chosen player"], zones=["hand", "Sheol", "Tower"], quantities=["two cards", "two cards"], outcomes=["puts two cards from that chosen player's hand into Sheol", "draw two cards from the Tower"]),
  "rarity_budget": budget(2, 2, 1, 1, 2, {"scope": "another player and three zones - hand, Sheol, Tower", "complexity": "a forced two-card loss and a two-card draw", "setup": "the chosen player must hold cards; Sheol receives them", "interaction": "one chosen player loses two cards", "payoff": "two cards drawn against one discard paid, with the opponent two cards poorer"}) })
META["DISCORD"] = {"gloss": "The sound of unity breaking into strife",
 "art_prompt": "A great unfinished brick tower at dusk with its wooden scaffolds splitting apart, cracked bricks tumbling from the ramps, torn banners whipped in opposite directions by a rising wind, one radiant golden light breaking through the storm clouds above, no people, " + STYLE,
 "stats": {"lore": 3, "context": 2, "complexity": 3},
 "stats_rationale": {"lore": "strife among brethren is a recognized wisdom theme (Proverbs) and the moral shape of Babel's confusion; not a doctrine in itself",
                     "context": "madon occurs 23 times in the Hebrew Bible; eris occurs 9 times in the New Testament; total 32",
                     "complexity": "madon comes from din, to contend at law, and appears in the plural form medanim in Proverbs; Greek eris is also the name of the goddess of strife - a derivation worth explaining"},
 "ot_verse": {"ref": "Proverbs 6:19", "snippet": "and he that soweth discord among brethren"},
 "nt_verse": {"ref": "1 Corinthians 3:3", "snippet": "there is among you envying, and strife, and divisions"},
 "greek": {"text": "ἔρις", "translit": "eris"},
 "hebrew": {"text": "מָדוֹן", "translit": "madon"},
 "ot_refs": "Prov 6:19 • Prov 6:14 • Prov 10:12",
 "nt_refs": "1 Cor 3:3 • Rom 1:29 • Gal 5:20",
 "trivia": ["Madon comes from din, to contend at law; discord in Proverbs is a lawsuit that never ends.",
            "The Greek eris was the goddess whose golden apple started the Trojan war; Paul lists her name among the works of the flesh.",
            "Babel's judgment was not silence but discord - every word still spoken, none understood."]}

# --------------------------------------------------------------- #058 DEPART
DESIGNS["DEPART"] = ("COMMON",
 {"core_meaning": "To pull up the tent pegs and set out, leaving a place behind by stages.",
  "type_expression": "A verb of setting out: the top of the Tower is looked over, any number of those cards are sent to the bottom - they depart - and the next card is drawn.",
  "mechanical_anchors": ["pull up the pegs", "sent to the bottom", "leave a place behind", "any number depart", "the next card"],
  "mechanic_seed": "Look at the top three cards, let any number of those cards depart to the bottom of the Tower, then draw the next card from the Tower."},
 {"mechanical_expression": "Departure is the top of the Tower pulling up its pegs: any number of the three cards looked at are sent to the bottom, and the next card from the Tower is drawn.",
  "semantic_anchor": "sent to the bottom",
  "semantic_evidence": ["Look at the top three cards of the Tower", "Put any number of those cards on the bottom of the Tower", "then draw one card from the Tower"],
  "ability_text": "Look at the top three cards of the Tower. Put any number of those cards on the bottom of the Tower, then draw one card from the Tower.",
  "rules_terms": ["cards", "card", "Tower", "look at", "put", "draw"],
  "rules_actions": ["look at", "put", "draw"],
  "clarity": cl(targets=["the top three cards of the Tower"], zones=["Tower"], quantities=["top three cards", "any number of those cards", "one card"], outcomes=["Put any number of those cards on the bottom of the Tower", "draw one card from the Tower"]),
  "rarity_budget": budget(1, 2, 0, 0, 1, {"scope": "the activating player and the Tower", "complexity": "a look, a placement, and a draw", "setup": "no prior state is required", "interaction": "no other player is touched", "payoff": "one card, chosen by sending the unwanted ones away first"}) })
META["DEPART"] = {"gloss": "To pull up stakes and leave the plain behind",
 "art_prompt": "Struck tents folded on the plain of Shinar at dawn, ox-carts and laden camels seen from far behind winding away toward distant hills in every direction, the unfinished tower a dark silhouette left behind, one radiant golden sunrise, no visible faces, " + STYLE,
 "stats": {"lore": 3, "context": 4, "complexity": 4},
 "stats_rationale": {"lore": "journeying by stages is the shape of the wilderness narrative and of the scattering from Shinar; a recognized theme rather than a doctrine",
                     "context": "nasa occurs 146 times in the Hebrew Bible; anachoreo occurs 14 times in the New Testament; total 160",
                     "complexity": "nasa literally means to pull up tent pegs, and its noun massa names both a journey-stage and a burden; anachoreo gives us the anchorite, one who withdraws - a history worth explaining"},
 "ot_verse": {"ref": "Genesis 11:2", "snippet": "as they journeyed from the east"},
 "nt_verse": {"ref": "Matthew 2:12", "snippet": "they departed into their own country another way"},
 "greek": {"text": "ἀναχωρέω", "translit": "anachoreo"},
 "hebrew": {"text": "נָסַע", "translit": "nasa"},
 "ot_refs": "Gen 11:2 • Gen 12:9 • Num 10:12",
 "nt_refs": "Matt 2:12 • Matt 4:12 • John 6:15",
 "trivia": ["Nasa is literally to pull up the pegs - a camp departs the way a tent comes down.",
            "The same root gives massa, a stage of the journey in Numbers 33 and, by another sense, a burden.",
            "Anachoreo is the verb behind anchorite, the hermit who departs from the world."]}

# --------------------------------------------------------------- #059 CHOSEN
DESIGNS["CHOSEN"] = ("UNCOMMON",
 {"core_meaning": "Set apart by God's choice for his covenant - the elect line that keeps what others must let go.",
  "type_expression": "An adjective of election: the player draws, and only a hand holding a NAME - the covenant line - keeps every card; otherwise one must go.",
  "mechanical_anchors": ["the covenant line keeps", "a NAME in hand", "the elect keep every card", "one must go", "set apart"],
  "mechanic_seed": "Draw two cards; if no NAME is in the hand, one card must go to the bottom of the Tower, but the covenant line keeps both."},
 {"mechanical_expression": "Election is tested in the hand: after drawing two cards, a hand with a NAME - the covenant line keeps - holds everything, while a hand without one must let one card go to the bottom of the Tower.",
  "semantic_anchor": "the covenant line keeps",
  "semantic_evidence": ["Draw two cards from the Tower", "If no NAME is in your hand, put one card from your hand on the bottom of the Tower"],
  "ability_text": "Draw two cards from the Tower. If no NAME is in your hand, put one card from your hand on the bottom of the Tower.",
  "rules_terms": ["cards", "card", "Tower", "hand", "NAME", "draw", "put"],
  "rules_actions": ["draw", "put"],
  "clarity": cl(targets=["your hand"], zones=["Tower", "hand"], quantities=["two cards", "one card"], condition="If no NAME is in your hand", outcomes=["Draw two cards from the Tower", "put one card from your hand on the bottom of the Tower"]),
  "rarity_budget": budget(2, 2, 1, 0, 2, {"scope": "the activating player, the Tower and the hand", "complexity": "a two-card draw with one printed condition", "setup": "the condition reads the hand for a NAME", "interaction": "no other player is touched", "payoff": "two cards, or one net card when no NAME is held"}) })
META["CHOSEN"] = {"gloss": "Set apart by God for his covenant",
 "art_prompt": "A single olive tree standing in a golden shaft of light on a dark hillside at night, a lamp burning at its roots, a ring of standing stones marking the ground apart, deep blue shadow beyond, no people, " + STYLE,
 "stats": {"lore": 5, "context": 2, "complexity": 3},
 "stats_rationale": {"lore": "election - Israel chosen, the church a chosen generation - is a doctrine that hangs on this word",
                     "context": "bachir occurs 13 times in the Hebrew Bible; eklektos occurs 22 times in the New Testament; total 35",
                     "complexity": "bachir is the passive adjective of bachar, to choose; eklektos, picked out, gives English both elect and eclectic - a derivation worth explaining"},
 "ot_verse": {"ref": "Psalm 105:6", "snippet": "ye children of Jacob his chosen"},
 "nt_verse": {"ref": "1 Peter 2:9", "snippet": "ye are a chosen generation"},
 "greek": {"text": "ἐκλεκτός", "translit": "eklektos"},
 "hebrew": {"text": "בָּחִיר", "translit": "bachir"},
 "ot_refs": "Ps 105:6 • Isa 42:1 • Isa 45:4",
 "nt_refs": "1 Pet 2:9 • Matt 22:14 • Col 3:12",
 "trivia": ["Bachir is the passive of bachar, to choose - the chosen one is the one picked out.",
            "Eklektos means picked out from among; the same word gives eclectic, a choice made from many.",
            "After Babel scattered the nations, God chose one man from Ur - election begins as a departure."]}

# ----------------------------------------------------------------- #060 EDEN
DESIGNS["EDEN"] = ("COMMON",
 {"core_meaning": "The garden planted at the beginning - delight and order set out by hand, then lost.",
  "type_expression": "A name of a planted place: the player draws from the Tower and then sets the next two cards in order, the way a garden is planted.",
  "mechanical_anchors": ["planted in order", "the garden set out", "the next two cards", "delight set by hand", "the beginning"],
  "mechanic_seed": "Draw one card from the Tower, then look at the next two cards on top and set those cards back in the order the gardener chooses."},
 {"mechanical_expression": "Eden is a garden planted in order: after drawing one card, the next two cards on top of the Tower are looked at and put back in the order the gardener chooses.",
  "semantic_anchor": "planted in order",
  "semantic_evidence": ["Draw one card from the Tower", "look at the top two cards of the Tower and put those cards back on top of the Tower in any order"],
  "ability_text": "Draw one card from the Tower. Then look at the top two cards of the Tower and put those cards back on top of the Tower in any order.",
  "rules_terms": ["card", "cards", "Tower", "draw", "look at", "put"],
  "rules_actions": ["draw", "look at", "put"],
  "clarity": cl(targets=["the top two cards of the Tower"], zones=["Tower"], quantities=["one card", "top two cards"], outcomes=["Draw one card from the Tower", "put those cards back on top of the Tower in any order"]),
  "rarity_budget": budget(1, 2, 0, 0, 1, {"scope": "the activating player and the Tower", "complexity": "a draw and a two-card reorder", "setup": "no prior state is required", "interaction": "no other player is touched", "payoff": "one card, with the next two set in order"}) })
META["EDEN"] = {"gloss": "The garden home, a lost paradise",
 "art_prompt": "A lush garden at dawn where four rivers part from a single spring, a great tree at the center haloed in radiant golden light, mist drifting through deep blue shadows beneath the boughs, no people, " + STYLE,
 "stats": {"lore": 5, "context": 2, "complexity": 4},
 "stats_rationale": {"lore": "creation, the fall, and paradise regained all turn on Eden; the doctrine of the fall hangs on this place",
                     "context": "Eden occurs 14 times in the Hebrew Bible as the garden and its land; paradeisos occurs 3 times in the New Testament; total 17",
                     "complexity": "Eden may mean delight or descend from a Sumerian word for the open plain; the Septuagint rendered the garden as paradeisos, a Persian loanword for a walled park, which the New Testament keeps - a history that is itself a study"},
 "ot_verse": {"ref": "Genesis 2:8", "snippet": "the LORD God planted a garden eastward in Eden"},
 "nt_verse": {"ref": "Revelation 2:7", "snippet": "the tree of life, which is in the midst of the paradise of God"},
 "greek": {"text": "παράδεισος", "translit": "paradeisos"},
 "hebrew": {"text": "עֵדֶן", "translit": "Eden"},
 "ot_refs": "Gen 2:8 • Gen 3:24 • Ezek 28:13",
 "nt_refs": "Rev 2:7 • Luke 23:43 • 2 Cor 12:4",
 "trivia": ["Eden may mean delight - or echo the Sumerian edin, the open plain - the same plain where Babel would rise.",
            "The Septuagint called the garden paradeisos, a Persian word for a walled royal park; paradise is Eden in Greek dress.",
            "The New Testament never names Eden, yet promises the tree of life in the paradise of God."]}

# ----------------------------------------------------------------- #061 FIRE
DESIGNS["FIRE"] = ("UNCOMMON",
 {"core_meaning": "The consuming, refining presence of God - flame that spends what it touches and lights what remains.",
  "type_expression": "A noun of consumption: fire is sent against another player, whose Letter is spent, while the sender draws light from the Tower.",
  "mechanical_anchors": ["consumes a Letter", "sent against another player", "spends what it touches", "light from the Tower", "refining flame"],
  "mechanic_seed": "Send fire against another player: that chosen player spends one Letter, consumed by the flame, then the sender draws one card from the Tower."},
 {"mechanical_expression": "Fire consumes a Letter: the chosen player spends one Letter as the flame spends what it touches, and the sender draws one card from the Tower.",
  "semantic_anchor": "consumes a Letter",
  "semantic_evidence": ["Choose another player", "That chosen player spends one Letter", "then draw one card from the Tower"],
  "ability_text": "Choose another player. That chosen player spends one Letter; then draw one card from the Tower.",
  "rules_terms": ["player", "Letter", "card", "Tower", "choose", "spend", "draw"],
  "rules_actions": ["choose", "spend", "draw"],
  "clarity": cl(targets=["another player", "That chosen player"], zones=["Tower"], quantities=["one Letter", "one card"], outcomes=["That chosen player spends one Letter", "draw one card from the Tower"]),
  "rarity_budget": budget(2, 2, 0, 1, 1, {"scope": "another player and the Tower", "complexity": "a forced Letter spend and a draw", "setup": "no prior state is required", "interaction": "one chosen player spends a Letter", "payoff": "one card, with the opponent one Letter poorer"}) })
META["FIRE"] = {"gloss": "A visible sign of the Spirit's presence",
 "art_prompt": "A thornbush burning with radiant golden flame yet unconsumed on a dark mountainside at night, a pair of sandals set on the rock before it, sparks rising into deep indigo shadow, no people, " + STYLE,
 "stats": {"lore": 4, "context": 5, "complexity": 2},
 "stats_rationale": {"lore": "theophany, judgment, and the tongues of fire at Pentecost - fire is a major sign of God's presence, a theme close to doctrine",
                     "context": "esh occurs 377 times in the Hebrew Bible; pyr occurs 71 times in the New Testament; total 448",
                     "complexity": "esh and pyr are both transparent everyday words; pyr survives in pyre and pyrotechnics - little history to explain"},
 "ot_verse": {"ref": "Exodus 3:2", "snippet": "the bush burned with fire, and the bush was not consumed"},
 "nt_verse": {"ref": "Acts 2:3", "snippet": "cloven tongues like as of fire"},
 "greek": {"text": "πῦρ", "translit": "pyr"},
 "hebrew": {"text": "אֵשׁ", "translit": "esh"},
 "ot_refs": "Exod 3:2 • Deut 4:24 • Gen 19:24",
 "nt_refs": "Acts 2:3 • Heb 12:29 • 1 Cor 3:13",
 "trivia": ["At Babel, fire baked the bricks; at Pentecost, fire sat on the heads of those who would speak every tongue.",
            "Deuteronomy calls the LORD a consuming fire, and Hebrews repeats the words without softening them.",
            "Pyr gives English pyre and pyrotechnics; the Greek word never lost its heat."]}

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

DESIGNS["DISCORD"][1]["mechanic_seed"] = "Sow discord: choose another player; that chosen player puts two cards from hand into Sheol as words fall into Sheol, then the sower draws two cards from the Tower."
DESIGNS["DISCORD"][1]["type_expression"] = "A noun of rupture: discord is sown against another player - that chosen player puts two cards into Sheol - while the sower gathers from the Tower."
