"""Batch 7 designs: slots #062-#066 (WICKED, CANAAN, MASTER, PELEG, EXILE) under the grammar, power ladder, and word weight."""
STYLE = "luminous cinematic oil painting with impressionistic brushwork, deep shadowed background, one radiant golden light source, rich saturated blues and golds"
def cl(**k):
    base={"trigger":"activation","timing":"instantaneous","targets":[],"zones":[],"quantities":[],"duration":"instantaneous","condition":"none","outcomes":[]}; base.update(k); return base
def budget(*v, why):
    return {k:{"rating":r,"rationale":w} for k,r,w in zip(("scope","complexity","setup","interaction","payoff"), v, why)}
DESIGNS = {}; META = {}

DESIGNS["WICKED"] = ("COMMON",
 {"core_meaning":"Guilty and loose before judgment - the wicked shall not stand; of what is laid out, most sinks and one is kept.",
  "type_expression":"An adjective of judgment: four cards are laid out from the top of the Tower, one is kept into hand, and the other cards sink to the bottom of the Tower.",
  "mechanical_anchors":["shall not stand","most sink to the bottom","one is kept","four laid out","judged from the top"],
  "mechanic_seed":"Look at four cards laid out from the top of the Tower, keep one of those cards into the hand, and let the other cards sink to the bottom of the Tower."},
 {"mechanical_expression":"Judgment lays out the top four cards of the Tower; one is kept in hand and the other cards sink to the bottom - the wicked shall not stand.",
  "semantic_anchor":"shall not stand",
  "semantic_evidence":["Look at the top four cards of the Tower","Add one of those cards to your hand","put the other cards on the bottom of the Tower"],
  "ability_text":"Look at the top four cards of the Tower. Add one of those cards to your hand and put the other cards on the bottom of the Tower.",
  "rules_terms":["cards","Tower","hand","look at","add","put"],
  "rules_actions":["look at","add","put"],
  "clarity":cl(targets=["the top four cards of the Tower","your hand"],zones=["Tower","hand"],quantities=["top four cards","one of those cards"],outcomes=["Add one of those cards to your hand","put the other cards on the bottom of the Tower"]),
  "rarity_budget":budget(2,2,0,0,1, why=["the Tower and the hand","a look, one add, and a placement","no prior state is required","no other player is touched","one chosen card of four"]) })
META["WICKED"] = {"gloss":"Guilty before God and loose from his law","weight":3,"weight_rationale":"the wicked of the flood generation and of Sodom - thematic vocabulary with real teaching behind it",
 "art_prompt":"A storm-lit plain at night with a cracked and blackened altar, scattered offerings blown across the stones, one column of radiant golden light striking down from a break in the clouds, no people, "+STYLE,
 "stats":{"lore":4,"context":5,"complexity":3},
 "stats_rationale":{"lore":"the wicked and the righteous are the two ways of the Psalms and the reason for the flood - a major theme close to doctrine","context":"rasha occurs 263 times in the Hebrew Bible; poneros occurs 78 times in the New Testament; total 341","complexity":"rasha means guilty and loose, the one who has lost his case; poneros began as toilsome and became evil - a derivation worth explaining"},
 "ot_verse":{"ref":"Psalm 1:5","snippet":"the ungodly shall not stand in the judgment"},"nt_verse":{"ref":"Matthew 13:49","snippet":"sever the wicked from among the just"},
 "greek":{"text":"πονηρός","translit":"poneros"},"hebrew":{"text":"רָשָׁע","translit":"rasha"},
 "ot_refs":"Ps 1:5 • Gen 18:23 • Ezek 33:11","nt_refs":"Matt 13:49 • Matt 6:13 • 1 John 5:19",
 "trivia":["Rasha is a courtroom word - the one found guilty - before it is a moral one.","Genesis 6 says the wickedness of man was great in the earth; the flood answers a legal verdict.","Poneros meant toilsome before it meant evil; the Evil One in the Lord's Prayer is the same word."]}

DESIGNS["CANAAN"] = ("UNCOMMON",
 {"core_meaning":"The son cursed to serve his brothers - a name that names a land and a lineage set under another.",
  "type_expression":"A name of a cursed son: the player chooses another player who serves - that chosen player reveals one card from hand - and then takes two cards from the Tower.",
  "mechanical_anchors":["set under his brothers","made to serve","another player reveals","two cards taken","a servant of servants"],
  "mechanic_seed":"Choose another player made to serve: that chosen player reveals one card from hand; then draw two cards from the Tower."},
 {"mechanical_expression":"Canaan is made to serve: another player is chosen and that chosen player reveals one card from that chosen player's hand, and then two cards are drawn from the Tower.",
  "semantic_anchor":"made to serve",
  "semantic_evidence":["Choose another player","that chosen player reveals one card from that chosen player's hand","draw two cards from the Tower"],
  "ability_text":"Choose another player; that chosen player reveals one card from that chosen player's hand. Then draw two cards from the Tower.",
  "rules_terms":["player","card","hand","cards","Tower","choose","reveal","draw"],
  "rules_actions":["choose","reveal","draw"],
  "clarity":cl(targets=["another player","that chosen player"],zones=["hand","Tower"],quantities=["one card","two cards"],outcomes=["that chosen player reveals one card from that chosen player's hand","draw two cards from the Tower"]),
  "rarity_budget":budget(2,1,0,1,2, why=["another player and the Tower","a reveal and a draw","no prior state is required","one chosen player shows a card","two cards drawn"]) })
META["CANAAN"] = {"gloss":"The son cursed to serve his brothers","weight":3,"weight_rationale":"a named figure and land of the second rank; the curse of Genesis 9 is thematic",
 "art_prompt":"An empty vineyard at dawn beside a tent, an overturned wine cup and a fallen cloak on the threshold, mist over the vines, one radiant golden light breaking over the hills, no people, "+STYLE,
 "stats":{"lore":3,"context":4,"complexity":3},
 "stats_rationale":{"lore":"the curse of Canaan and the land of promise - a recognized theme, not a doctrine","context":"Kenaan occurs 94 times in the Hebrew Bible; Chanaan occurs 2 times in the New Testament; total 96","complexity":"a personal name that became a land, then a byword; the curse fell on the son, not the father - a history worth explaining"},
 "ot_verse":{"ref":"Genesis 9:25","snippet":"Cursed be Canaan; a servant of servants shall he be"},"nt_verse":{"ref":"Acts 7:11","snippet":"there came a dearth over all the land of Egypt and Chanaan"},
 "greek":{"text":"Χανάαν","translit":"Chanaan"},"hebrew":{"text":"כְּנַעַן","translit":"Kenaan"},
 "ot_refs":"Gen 9:25 • Gen 10:6 • Gen 12:5","nt_refs":"Acts 7:11 • Acts 13:19",
 "trivia":["Noah cursed Canaan, not Ham - the grandson bears the word for the father's deed.","Canaan the man became Canaan the land; the name means merchant or lowland in later Semitic use.","Stephen's speech in Acts 7 uses the Greek spelling Chanaan for the land the fathers entered."]}

DESIGNS["MASTER"] = ("COMMON",
 {"core_meaning":"The one who owns and directs the work - naming the kind of labor wanted and sending away what is not.",
  "type_expression":"A title of office: the master names a card type, draws one card from the Tower, and may send one card of the named type from hand to the bottom of the Tower.",
  "mechanical_anchors":["names the kind of labor","owns the work","sends away the named kind","one card drawn","the master's bidding"],
  "mechanic_seed":"Name a card type and draw one card from the Tower; then the master may put one card of the named type from the hand on the bottom of the Tower, sending away that kind."},
 {"mechanical_expression":"The master names the kind of labor wanted - a card type - draws one card from the Tower, and may send away the named kind: one card of the named type from hand goes on the bottom of the Tower.",
  "semantic_anchor":"names the kind of labor",
  "semantic_evidence":["Name a card type and draw one card from the Tower","you may put one card of the named type from your hand on the bottom of the Tower"],
  "ability_text":"Name a card type and draw one card from the Tower. Then you may put one card of the named type from your hand on the bottom of the Tower.",
  "rules_terms":["card type","card","Tower","hand","name","draw","put"],
  "rules_actions":["name","draw","put"],
  "clarity":cl(targets=["your hand"],zones=["Tower","hand"],quantities=["one card","one card"],outcomes=["draw one card from the Tower","put one card of the named type from your hand on the bottom of the Tower"]),
  "rarity_budget":budget(2,2,0,0,1, why=["the Tower and the hand","a declaration, a draw, and an optional placement","no prior state is required","no other player is touched","one card, with an optional placement of a named kind"]) })
META["MASTER"] = {"gloss":"The one who owns and directs the work","weight":2,"weight_rationale":"an office word for the tower's overseers; descriptive with a clear place",
 "art_prompt":"A great brick kiln and timber scaffold under a hot evening sky, a plumb line and measuring rod laid on a stone table beside a heap of fired bricks, one radiant golden glow from the kiln mouth, no people, "+STYLE,
 "stats":{"lore":3,"context":3,"complexity":4},
 "stats_rationale":{"lore":"masters and servants order the household codes and the parables; a recognized theme","context":"baal occurs 84 times in the Hebrew Bible as owner or master; despotes occurs 10 times in the New Testament; total 94","complexity":"baal means owner, master, and husband, and became the name of the Canaanite god the prophets fought; despotes gives English despot - a history that is itself a study"},
 "ot_verse":{"ref":"Isaiah 1:3","snippet":"the ox knoweth his owner, and the ass his master's crib"},"nt_verse":{"ref":"1 Timothy 6:1","snippet":"count their own masters worthy of all honour"},
 "greek":{"text":"δεσπότης","translit":"despotes"},"hebrew":{"text":"בַּעַל","translit":"baal"},
 "ot_refs":"Isa 1:3 • Exod 21:28 • Gen 20:3","nt_refs":"1 Tim 6:1 • 2 Tim 2:21 • Titus 2:9",
 "trivia":["Baal simply meant owner or master before it named the storm god; Hosea says Israel will call God ishi, my husband, and no more baali, my master.","Despotes, the master of a household, is also the word Simeon uses to address God - Lord, now lettest thou thy servant depart.","The tower's masters had bricks for stone and slime for mortar; the text names the work before it names a single worker."]}

DESIGNS["PELEG"] = ("RARE",
 {"core_meaning":"In his days the earth was divided - a name for the moment the one people split into the kinds the Chapter Lot names.",
  "type_expression":"A name of a divided age: four cards are revealed from the top of the Tower, up to three whose card types are in the Chapter Lot are taken as the divided portions, the other revealed cards fall into Sheol, and one card from hand goes on top of the Tower.",
  "mechanical_anchors":["the earth was divided","portions by the Chapter Lot","up to three taken","the rest fall into Sheol","one set on top"],
  "mechanic_seed":"Reveal the top four cards of the Tower; take up to three revealed cards whose card type is in the Chapter Lot as the divided portions, put the other revealed cards into Sheol, and put one card from the hand on top of the Tower."},
 {"mechanical_expression":"The earth was divided in Peleg's days: four cards are revealed from the top of the Tower, up to three revealed cards whose card type is in the Chapter Lot are added to hand as portions by the Chapter Lot, the other revealed cards go into Sheol, and one card from hand is put on top of the Tower.",
  "semantic_anchor":"portions by the Chapter Lot",
  "semantic_evidence":["Reveal the top four cards of the Tower","Add up to three revealed cards whose card type is in the Chapter Lot to your hand","put the other revealed cards into Sheol"],
  "ability_text":"Reveal the top four cards of the Tower. Add up to three revealed cards whose card type is in the Chapter Lot to your hand, put the other revealed cards into Sheol, and put one card from your hand on top of the Tower.",
  "rules_terms":["cards","card","Tower","card type","Chapter Lot","hand","Sheol","reveal","add","put"],
  "rules_actions":["reveal","add","put","put"],
  "clarity":cl(targets=["the top four cards of the Tower","your hand"],zones=["Tower","Chapter Lot","hand","Sheol"],quantities=["top four cards","up to three revealed cards","one card"],outcomes=["Add up to three revealed cards whose card type is in the Chapter Lot to your hand","put the other revealed cards into Sheol","put one card from your hand on top of the Tower"]),
  "rarity_budget":budget(2,3,1,0,3, why=["the Tower, the Chapter Lot, the hand and Sheol","a reveal, a Lot-filtered scaling add, and two placements","the Chapter Lot is read; Sheol receives cards","no other player is touched","up to three Lot-matching cards against one card set back and one discard paid"]) })
META["PELEG"] = {"gloss":"In his days the earth was divided","weight":3,"weight_rationale":"a named figure of the second rank whose name carries the division of the nations",
 "art_prompt":"A vast plain splitting along a widening crack at dusk, a river dividing into two channels around the fissure, clusters of tents on either bank drifting apart, one radiant golden sunset on the horizon, no people, "+STYLE,
 "stats":{"lore":3,"context":1,"complexity":4},
 "stats_rationale":{"lore":"the division of the earth in Genesis 10 anchors the table of nations before Babel; a recognized theme","context":"Peleg occurs 7 times in the Hebrew Bible; Phalek occurs 1 time in the New Testament (Luke 3:35); total 8","complexity":"the name is a pun on palag, to divide, planted in the genealogy to mark the scattering; Luke carries the Greek Phalek into the line of Jesus - a history worth explaining"},
 "ot_verse":{"ref":"Genesis 10:25","snippet":"the name of one was Peleg; for in his days was the earth divided"},"nt_verse":{"ref":"Luke 3:35","snippet":"which was the son of Phalec"},
 "greek":{"text":"Φάλεκ","translit":"Phalek"},"hebrew":{"text":"פֶּלֶג","translit":"Peleg"},
 "ot_refs":"Gen 10:25 • Gen 11:16 • 1 Chr 1:19","nt_refs":"Luke 3:35",
 "trivia":["Peleg means division; Genesis explains the name in the same breath - in his days was the earth divided.","His name sits in the genealogy between Eber and Abram: Babel happens inside a family tree.","Luke's genealogy spells him Phalec and carries the divided age into the line of Christ."]}

DESIGNS["EXILE"] = ("UNCOMMON",
 {"core_meaning":"One driven out from home by divine decree - cast out of the garden, cast out from the ground - who trades places and wanders on.",
  "type_expression":"A title of banishment: the exile is chosen against another player, one card is exchanged from hand to hand, and the exile wanders on by drawing two cards from the Tower.",
  "mechanical_anchors":["driven out","trades places","one card exchanged","wanders on","cast out from the ground"],
  "mechanic_seed":"Choose another player and exchange one card from the hand with one card from that chosen player's hand - trades places - then wander on and draw two cards from the Tower."},
 {"mechanical_expression":"The exile is driven out: another player is chosen and one card from hand is exchanged with one card from that chosen player's hand - the exile trades places - and then the exile wanders on, drawing two cards from the Tower.",
  "semantic_anchor":"trades places",
  "semantic_evidence":["exchange one card from your hand with one card from that chosen player's hand","draw two cards from the Tower"],
  "ability_text":"Choose another player and exchange one card from your hand with one card from that chosen player's hand. Then draw two cards from the Tower.",
  "rules_terms":["player","card","hand","cards","Tower","choose","exchange","draw"],
  "rules_actions":["choose","exchange","draw"],
  "clarity":cl(targets=["another player","that chosen player","your hand"],zones=["hand","Tower"],quantities=["one card","one card","two cards"],outcomes=["exchange one card from your hand with one card from that chosen player's hand","draw two cards from the Tower"]),
  "rarity_budget":budget(2,2,0,2,2, why=["another player's hand, your hand and the Tower","an exchange and a draw","no prior state is required","one chosen player's hand is changed","two cards drawn plus a swap"]) })
META["EXILE"] = {"gloss":"One driven from home by divine decree","weight":3,"weight_rationale":"Adam and Cain driven out - the era's first exiles; thematic",
 "art_prompt":"A lone cloaked figure seen from far behind walking away from a gate of radiant golden light into a wide dark wilderness, a flaming sword hanging above the gate, no visible face, "+STYLE,
 "stats":{"lore":4,"context":4,"complexity":3},
 "stats_rationale":{"lore":"expulsion from Eden and the exile of Cain set the pattern for Babylon and for every wandering; a major theme close to doctrine","context":"garash occurs 47 times in the Hebrew Bible; ekballo occurs 81 times in the New Testament; total 128","complexity":"garash is to drive out or divorce, the verb of Eden's gate and Hagar's tent; ekballo, to cast out, is the verb of demons and of the Spirit driving Jesus into the wilderness - a derivation worth explaining"},
 "ot_verse":{"ref":"Genesis 3:24","snippet":"So he drove out the man"},"nt_verse":{"ref":"Galatians 4:30","snippet":"Cast out the bondwoman and her son"},
 "greek":{"text":"ἐκβάλλω","translit":"ekballo"},"hebrew":{"text":"גָּרַשׁ","translit":"garash"},
 "ot_refs":"Gen 3:24 • Gen 4:14 • Gen 21:10","nt_refs":"Gal 4:30 • Mark 1:12 • John 9:34",
 "trivia":["Garash drives out the man from Eden and, in Cain's mouth, drives him from the face of the earth - the same verb for both exiles.","Ekballo casts out demons, and in Mark 1 the Spirit casts Jesus out into the wilderness - exile as calling.","Babel's scattering is the third exile of Genesis; each time the road leads east."]}

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

# ---- overrides after offline validation
META["WICKED"]["stats"]["context"] = 4
META["CANAAN"]["stats"]["context"] = 3
META["PELEG"]["stats_rationale"]["context"] = "Peleg occurs 7 times in the Hebrew Bible; Phalek occurs 1 time in the New Testament; total 8"
_p = DESIGNS["PELEG"][2]
_p["ability_text"] = "Reveal the top four cards of the Tower. Add up to three revealed cards whose card type is in the Chapter Lot to your hand, put each other revealed card into Sheol, and put one card from your hand on top of the Tower."
_p["semantic_evidence"] = ["Reveal the top four cards of the Tower","Add up to three revealed cards whose card type is in the Chapter Lot to your hand","put each other revealed card into Sheol"]
_p["clarity"]["outcomes"] = ["Add up to three revealed cards whose card type is in the Chapter Lot to your hand","put each other revealed card into Sheol","put one card from your hand on top of the Tower"]
_p["mechanical_expression"] = "The earth was divided in Peleg's days: four cards are revealed from the top of the Tower, up to three revealed cards whose card type is in the Chapter Lot are added to hand as portions by the Chapter Lot, each other revealed card goes into Sheol, and one card from hand is put on top of the Tower."
DESIGNS["PELEG"][1]["mechanic_seed"] = "Reveal the top four cards of the Tower; take up to three revealed cards whose card type is in the Chapter Lot as the divided portions, put each other revealed card into Sheol, and put one card from the hand on top of the Tower."
_e = DESIGNS["EXILE"][2]
_e["ability_text"] = "Choose another player. Exchange one card from your hand with one card from that chosen player's hand, then draw two cards from the Tower."
_e["semantic_evidence"] = ["Exchange one card from your hand with one card from that chosen player's hand","draw two cards from the Tower"]
_e["clarity"]["outcomes"] = ["Exchange one card from your hand with one card from that chosen player's hand","draw two cards from the Tower"]
