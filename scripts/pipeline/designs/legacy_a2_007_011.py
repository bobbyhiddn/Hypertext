"""Module A2 regen: legacy slots #007-#011 (EARTH, STONE, CITY, NAME, DESCEND) redesigned
under the grammar, the power ladder, word weight, the stat rubric, the mechanic axes and
the art subject/lighting rules.

The WORD of each slot is unchanged and the printed lemmas stay as they were, with one
correction: STONE printed Greek lithos, which is BRICK's printed lemma, so STONE now
prints petra with an NT verse that carries it. Ability, art, stats, weight, verses and
trivia are new.
"""
from hypertext.cards.art_motifs import load_art_standards, style_suffix

_ART = load_art_standards("series/2026-Q1")
def S(name):
    return style_suffix(_ART, name)

def cl(**k):
    base={"trigger":"activation","timing":"instantaneous","targets":[],"zones":[],"quantities":[],"duration":"instantaneous","condition":"none","outcomes":[]}; base.update(k); return base
def budget(*v, why):
    return {k:{"rating":r,"rationale":w} for k,r,w in zip(("scope","complexity","setup","interaction","payoff"), v, why)}
DESIGNS = {}; META = {}

# ---------------------------------------------------------------- COMMON
DESIGNS["EARTH"] = ("COMMON",
 {"core_meaning":"The ground, and the whole land the ground makes up - the earth was filled with violence; what the earth holds is what fills it.",
  "type_expression":"A noun of extent: the whole earth is looked over at once, the one word that fills it - CONTEXT four or more - is taken up out of the ground, and the rest are set back in place on top.",
  "mechanical_anchors":["the whole earth looked over at once","the one that fills the earth","the earth was filled","set back in place on top","CONTEXT four or more"],
  "mechanic_seed":"Look at the top five cards of the Tower, the whole earth looked over at once; add one of those cards that has CONTEXT four or more to your hand, the one that fills the earth, and put the other cards on top of the Tower, set back in place."},
 {"mechanical_expression":"The whole earth is looked over at once - five cards together - and the one that fills the earth, with CONTEXT four or more, is taken into the hand, while the other cards are set back in place on top of the Tower.",
  "semantic_anchor":"the one that fills the earth",
  "semantic_evidence":["Look at the top five cards of the Tower","Add one of those cards that has CONTEXT four or more to your hand","put the other cards on top of the Tower"],
  "ability_text":"Look at the top five cards of the Tower. Add one of those cards that has CONTEXT four or more to your hand and put the other cards on top of the Tower.",
  "rules_terms":["cards","Tower","CONTEXT","hand","card","look at","add","put"],
  "rules_actions":["look at","add","put"],
  "clarity":cl(targets=["the top five cards of the Tower","your hand"],zones=["Tower","hand"],quantities=["top five cards","one of those cards"],outcomes=["Add one of those cards that has CONTEXT four or more to your hand","put the other cards on top of the Tower"]),
  "rarity_budget":budget(2,2,0,0,1, why=["the Tower and the hand","one filtered add and one placement","no prior state is required","no other player is touched","one card taken, chosen by how far it fills the earth, out of five seen"]) })
META["EARTH"] = {"gloss":"The ground; the whole land it makes up","weight":2,"weight_rationale":"the ground the whole era is played out on - corrupted, flooded, dried and repopulated - but the word is the setting rather than a named agent, place or event the era turns on, so it stays at 2 and prints COMMON",
 "art_prompt":"A close view of ploughed ground, dark cracked loam broken into clods along one furrow, a flint blade and the dry white root of a thorn turned up in the topsoil, no people, "+S("golden"),
 "stats":{"lore":3,"context":5,"complexity":3},
 "stats_rationale":{"lore":"the printed verses charge the earth itself with corruption before the flood and promise it to the meek as an inheritance - a recognized theme of the era with clear teaching, though the doctrine hangs on judgment and promise rather than on the ground","context":"eretz occurs 2504 times in the Hebrew Bible; ge occurs 250 times in the New Testament; total 2754","complexity":"eretz is at once the whole earth and one particular country, so the same word is world in Genesis 1:1 and land in the land of Canaan, and a translator must choose which is meant almost line by line"},
 "ot_verse":{"ref":"Genesis 6:11","snippet":"The earth also was corrupt before God, and the earth was filled with violence"},"nt_verse":{"ref":"Matthew 5:5","snippet":"Blessed are the meek: for they shall inherit the earth"},
 "greek":{"text":"γῆ","translit":"ge"},"hebrew":{"text":"אֶרֶץ","translit":"eretz"},
 "ot_refs":"Gen 6:11 • Gen 1:1 • Gen 11:1","nt_refs":"Matt 5:5 • Matt 5:18 • Rev 21:1",
 "trivia":["Genesis 6:11 charges the earth itself, not only the people on it: the ground is corrupt before God and filled with violence.","Eretz is both the planet and a parcel of it - the earth of Genesis 1:1 and the land of Canaan are the same noun.","Matthew 5:5 quotes Psalm 37:11, where the inheritance promised is eretz, the land; the meek inherit either a country or the whole world depending on which word you hear."]}

DESIGNS["STONE"] = ("COMMON",
 {"core_meaning":"Hard rock, the material a thing is founded on and built out of - they had brick for stone; stone is not made, it is found, and it does not move.",
  "type_expression":"A noun of substance: the courses at the foot of the Tower are searched over, the solid thing among them is lifted out, and the rest are laid back down under.",
  "mechanical_anchors":["the courses at the foot searched over","the solid thing among them","they had brick for stone","laid back down under","a card that is a NOUN"],
  "mechanic_seed":"Look at the bottom three cards of the Tower, the courses at the foot searched over; add one of those cards that is a NOUN to your hand, the solid thing among them lifted out, and put the other cards on the bottom of the Tower, laid back down under."},
 {"mechanical_expression":"The courses at the foot of the Tower are searched over, and the solid thing among them - a card that is a NOUN - is lifted out into the hand, while the other cards are laid back down on the bottom of the Tower.",
  "semantic_anchor":"the solid thing among them",
  "semantic_evidence":["Look at the bottom three cards of the Tower","Add one of those cards that is a NOUN to your hand","put the other cards on the bottom of the Tower"],
  "ability_text":"Look at the bottom three cards of the Tower. Add one of those cards that is a NOUN to your hand and put the other cards on the bottom of the Tower.",
  "rules_terms":["cards","Tower","NOUN","hand","card","look at","add","put"],
  "rules_actions":["look at","add","put"],
  "clarity":cl(targets=["the bottom three cards of the Tower","your hand"],zones=["Tower","hand"],quantities=["bottom three cards","one of those cards"],outcomes=["Add one of those cards that is a NOUN to your hand","put the other cards on the bottom of the Tower"]),
  "rarity_budget":budget(2,2,0,0,1, why=["the Tower and the hand","one filtered add and one placement","no prior state is required","no other player is touched","one card taken, and only the solid kind, out of three seen at the foot"]) })
META["STONE"] = {"gloss":"Hard rock; the found material a thing is founded on","weight":2,"weight_rationale":"the material Babel's builders did not have and counterfeited with brick, and the era's measure of what lasts - a descriptive material word with a clear place, not a named agent, place or event the era turns on, so it stays at 2 and prints COMMON",
 "art_prompt":"A single undressed limestone block half-buried at the foot of a rising course of mud brick, chisel marks raw across its face, an iron wedge and a coil of measuring cord left lying on it, the red glow of a brick kiln beating across the stone, no people, "+S("firelight"),
 "stats":{"lore":3,"context":4,"complexity":3},
 "stats_rationale":{"lore":"the printed verses set the builders' want of stone on the plain beside the rock a church is founded on - a recognized theme with clear teaching, though the doctrine rests on the builder rather than on the material","context":"eben occurs 272 times in the Hebrew Bible; petra occurs 15 times in the New Testament; total 287","complexity":"Genesis 11:3 turns on a near-pun, lebenah put in the place of eben - brick for stone - and Greek divides what Hebrew keeps whole, lithos for a stone a man can lift and petra for living rock, so one eben is translated two ways by size and setting"},
 "ot_verse":{"ref":"Genesis 11:3","snippet":"And they had brick for stone, and slime had they for morter"},"nt_verse":{"ref":"Matthew 16:18","snippet":"upon this rock I will build my church"},
 "greek":{"text":"πέτρα","translit":"petra"},"hebrew":{"text":"אֶבֶן","translit":"eben"},
 "ot_refs":"Gen 11:3 • Gen 2:12 • Gen 28:18","nt_refs":"Matt 16:18 • Matt 7:24 • 1 Cor 10:4",
 "trivia":["There is no building stone in the alluvial plain of Shinar, so Babel's builders burned brick for it and used slime for morter - a city of substitutes from the first course up.","Greek splits the one Hebrew word: lithos is a stone a man can lift and petra is the rock a house is founded on, and both stand for eben.","Matthew 16:18 sets a name against a noun, Petros against petra - masculine for the man, feminine for the rock - a pun that works only in Greek."]}

DESIGNS["CITY"] = ("COMMON",
 {"core_meaning":"A walled settlement with one gate - let us build us a city and a tower; a city takes in whom its charter calls for and leaves the rest outside the wall.",
  "type_expression":"A noun of settlement: four come up to the gate in the open, the one the common charter calls for is taken in through it, and the others are set back outside the wall.",
  "mechanical_anchors":["come up to the gate in the open","taken in through the gate","let us build us a city","set back outside the wall","the one the common charter calls for"],
  "mechanic_seed":"Reveal the top four cards of the Tower, four come up to the gate in the open; add one revealed card whose card type is in the Chapter Lot to your hand, the one the common charter calls for taken in through the gate, and put the other cards on top of the Tower, set back outside the wall."},
 {"mechanical_expression":"Four cards come up to the gate in the open and the one the common charter calls for - a revealed card whose card type is in the Chapter Lot - is taken in through the gate into the hand, while the other cards are set back outside the wall on top of the Tower.",
  "semantic_anchor":"taken in through the gate",
  "semantic_evidence":["Reveal the top four cards of the Tower","Add one revealed card whose card type is in the Chapter Lot to your hand","put the other cards on top of the Tower"],
  "ability_text":"Reveal the top four cards of the Tower. Add one revealed card whose card type is in the Chapter Lot to your hand and put the other cards on top of the Tower.",
  "rules_terms":["cards","Tower","card","card type","Chapter Lot","hand","reveal","add","put"],
  "rules_actions":["reveal","add","put"],
  "clarity":cl(targets=["the top four cards of the Tower","your hand"],zones=["Tower","Chapter Lot","hand"],quantities=["top four cards","one revealed card"],outcomes=["Add one revealed card whose card type is in the Chapter Lot to your hand","put the other cards on top of the Tower"]),
  "rarity_budget":budget(2,2,0,0,1, why=["the Tower, the Chapter Lot and the hand","one filtered add and one placement","the Chapter Lot is read as it lies, with no prior state built","no other player is touched","one card taken in out of four shown, and only if the common charter calls for its type"]) })
META["CITY"] = {"gloss":"A walled settlement; a gathering behind one gate","weight":2,"weight_rationale":"what Babel's builders set out to make and the first thing Cain builds after the curse - a settlement word with a clear place in the era, but the named event is Babel itself rather than the noun, so it stays at 2 and prints COMMON",
 "art_prompt":"A mudbrick gateway at the end of a narrow lane, its heavy cedar doors standing open on a rutted threshold, the unfinished tower rising over flat rooftops beyond, no people, "+S("golden"),
 "stats":{"lore":3,"context":5,"complexity":3},
 "stats_rationale":{"lore":"the printed verses set the city the builders raised for their own name beside the city set on a hill that cannot be hid - a recognized theme of the era with clear teaching, though what is taught hangs on the builders' purpose rather than on the walls","context":"ir occurs 1093 times in the Hebrew Bible; polis occurs 162 times in the New Testament; total 1255","complexity":"ir covers everything from a walled capital to a hamlet - Cain builds one for a single household - while Greek polis carries a civic and political sense Hebrew never had, so the Septuagint quietly turns every Hebrew settlement into a city-state"},
 "ot_verse":{"ref":"Genesis 11:4","snippet":"let us build us a city and a tower, whose top may reach unto heaven"},"nt_verse":{"ref":"Matthew 5:14","snippet":"A city that is set on an hill cannot be hid"},
 "greek":{"text":"πόλις","translit":"polis"},"hebrew":{"text":"עִיר","translit":"ir"},
 "ot_refs":"Gen 11:4 • Gen 4:17 • Gen 11:8","nt_refs":"Matt 5:14 • Heb 11:10 • Rev 21:2",
 "trivia":["The first city in Scripture is built by Cain, the man sentenced to be a fugitive and a vagabond, and he calls it after the name of his son.","Genesis 11 names the city more often than the tower: the LORD comes down to see the city and the tower, and what the builders leave off building is the city.","Hebrews 11:10 answers Babel exactly - Abraham looked for a city which hath foundations, whose builder and maker is God."]}

DESIGNS["NAME"] = ("COMMON",
 {"core_meaning":"The word a thing is called by, and the standing that word carries - whatsoever Adam called every living creature, that was the name thereof.",
  "type_expression":"A noun of calling: four names are read over together, the one set above every other by the weight of its tongue is called into the hand, and the lesser names are laid under.",
  "mechanical_anchors":["four names read over together","set above every other","a name which is above every name","the lesser names laid under","COMPLEXITY four or more"],
  "mechanic_seed":"Look at the top four cards of the Tower, four names read over together; add one of those cards that has COMPLEXITY four or more to your hand, set above every other by the weight of its tongue, and put the other cards on the bottom of the Tower, the lesser names laid under."},
 {"mechanical_expression":"Four names are read over together and one is set above every other: the card with COMPLEXITY four or more is called into the hand, and the other cards are laid under on the bottom of the Tower.",
  "semantic_anchor":"set above every other",
  "semantic_evidence":["Look at the top four cards of the Tower","Add one of those cards that has COMPLEXITY four or more to your hand","put the other cards on the bottom of the Tower"],
  "ability_text":"Look at the top four cards of the Tower. Add one of those cards that has COMPLEXITY four or more to your hand and put the other cards on the bottom of the Tower.",
  "rules_terms":["cards","Tower","COMPLEXITY","hand","card","look at","add","put"],
  "rules_actions":["look at","add","put"],
  "clarity":cl(targets=["the top four cards of the Tower","your hand"],zones=["Tower","hand"],quantities=["top four cards","one of those cards"],outcomes=["Add one of those cards that has COMPLEXITY four or more to your hand","put the other cards on the bottom of the Tower"]),
  "rarity_budget":budget(2,2,0,0,1, why=["the Tower and the hand","one filtered add and one placement","no prior state is required","no other player is touched","one card called into the hand out of four read, and only when its tongue is weighty enough"]) })
META["NAME"] = {"gloss":"The word a thing is called by; the standing it carries","weight":3,"weight_rationale":"calling upon the name of the LORD and making us a name at Babel are two of the turns the era is built on, and the noun stands behind the patriarch Shem - thematic vocabulary with real teaching, while the promise the era hangs on is carried by COVENANT, so NAME stays at 3",
 "art_prompt":"A crested hoopoe on a low branch, a young ibex and a striped lizard on warm stone, all three held still at the mouth of a walled garden as though waiting to be called, no people, "+S("golden"),
 "stats":{"lore":3,"context":5,"complexity":4},
 "stats_rationale":{"lore":"the printed verses give the naming of every living creature and the name given above every name - a recognized theme of the era with clear teaching, though in Genesis what is taught hangs on who does the calling rather than on the noun","context":"shem occurs 864 times in the Hebrew Bible; onoma occurs 231 times in the New Testament; total 1095","complexity":"shem is a standing rather than a label - to make a name is to seize a reputation, to call on the name is to worship, and to cut off a name is to end a house - and it is a proper name besides, so Babel's builders grasp at shem two chapters after Shem has been given one"},
 "ot_verse":{"ref":"Genesis 2:19","snippet":"whatsoever Adam called every living creature, that was the name thereof"},"nt_verse":{"ref":"Philippians 2:9","snippet":"given him a name which is above every name"},
 "greek":{"text":"ὄνομα","translit":"onoma"},"hebrew":{"text":"שֵׁם","translit":"shem"},
 "ot_refs":"Gen 2:19 • Gen 4:26 • Gen 11:4","nt_refs":"Phil 2:9 • Acts 4:12 • John 1:12",
 "trivia":["Genesis 2:19 is the first recorded speech of a man: God brings the creatures to Adam to see what he would call them, and whatever he calls them stands.","Babel's builders say let us make us a name, two chapters after a son of Noah has been given the name that simply means Name.","To act in a name, in both Testaments, is to act in the authority the name carries - which is why calling on the name of the LORD, begun in the days of Enos, counts as worship."]}

# ---------------------------------------------------------------- UNCOMMON
DESIGNS["DESCEND"] = ("UNCOMMON",
 {"core_meaning":"To come down from a higher place to a lower - and the LORD came down to see the city and the tower; whatever descends leaves the height it stood at.",
  "type_expression":"A verb of downward motion: the three highest courses of the Tower come down into Sheol, and the going down is written out as a Letter.",
  "mechanical_anchors":["the three highest courses come down","down into Sheol","the LORD came down to see","the going down written out as a Letter","the height is left behind"],
  "mechanic_seed":"Put the top three cards of the Tower into Sheol, the three highest courses come down as the LORD came down to see; then gain one Letter, the going down written out as a Letter."},
 {"mechanical_expression":"The three highest courses of the Tower come down into Sheol, and the going down is written out as a Letter gained.",
  "semantic_anchor":"the three highest courses come down",
  "semantic_evidence":["Put the top three cards of the Tower into Sheol","gain one Letter"],
  "ability_text":"Put the top three cards of the Tower into Sheol. Then gain one Letter.",
  "rules_terms":["cards","Tower","Sheol","Letter","put","gain"],
  "rules_actions":["put","gain"],
  "clarity":cl(targets=["the top three cards of the Tower"],zones=["Tower","Sheol","Letters"],quantities=["top three cards","one Letter"],outcomes=["Put the top three cards of the Tower into Sheol","gain one Letter"]),
  "rarity_budget":budget(2,2,1,0,3, why=["the Tower, Sheol and your Letters","one placement and one gain","the top of the Tower must be spent down into Sheol before the Letter is written","no other player is touched","a Letter, worth three cards, for bringing the height down"]) })
META["DESCEND"] = {"gloss":"To come down from a higher place to a lower","weight":3,"weight_rationale":"the LORD's coming down to see the city and the tower is the hinge the Babel account turns on, and the same verb carries the going down to Egypt and the going down to the grave - thematic vocabulary with real teaching, while the named event is Babel itself, so DESCEND stays at 3 and prints UNCOMMON",
 "art_prompt":"A steep flight of worn stone steps cut down into a narrow rock-hewn shaft, the treads dwindling into darkness below, a frayed rope left coiled on the topmost tread, no people, "+S("golden"),
 "stats":{"lore":3,"context":5,"complexity":2},
 "stats_rationale":{"lore":"the printed verses give the LORD coming down to see what the builders had made and the Lord himself descending from heaven with a shout - a recognized theme with clear teaching, though what is taught hangs on who descends rather than on the verb","context":"yarad occurs 380 times in the Hebrew Bible; katabaino occurs 81 times in the New Testament; total 461","complexity":"a plain verb of direction, with one thing to explain: Hebrew keeps it literal for the road to Egypt and for the descent to the grave alike, so travel and death share a word, and Greek katabaino inherits the double sense unchanged"},
 "ot_verse":{"ref":"Genesis 11:5","snippet":"And the LORD came down to see the city and the tower, which the children of men builded"},"nt_verse":{"ref":"1 Thessalonians 4:16","snippet":"the Lord himself shall descend from heaven with a shout"},
 "greek":{"text":"καταβαίνω","translit":"katabaino"},"hebrew":{"text":"יָרַד","translit":"yarad"},
 "ot_refs":"Gen 11:5 • Gen 11:7 • Gen 12:10","nt_refs":"1 Thess 4:16 • John 1:51 • John 6:38",
 "trivia":["Genesis 11:5 is quietly ironic: the tower's top was to reach unto heaven, and the LORD has to come down to see it.","Genesis 11:7 has God say let us go down - a second descent three verses later, and that one scatters the languages.","The same verb sends Abram down into Egypt and brings Jacob's gray hairs down to Sheol; in Hebrew, direction and destiny share one word."]}

# ---------------------------------------------------------------- UNCOMMON
DESIGNS["DESCEND"] = ("UNCOMMON",
 {"core_meaning":"To come down from a higher place to a lower - the LORD came down to see the city and the tower; and no man hath ascended up to heaven, but he that came down from heaven.",
  "type_expression":"A verb of going down: one card is sent down into Sheol ahead of you, then you go down after it and fetch up the weightiest word lying there, and one more card comes up from the Tower.",
  "mechanical_anchors":["sent down into Sheol ahead of you","fetched up from below","the weightiest word lying there","the LORD came down to see","LORE four or more"],
  "mechanic_seed":"Put one card from your hand into Sheol, sent down into Sheol ahead of you. Then choose one card in Sheol that has LORE four or more, the weightiest word lying there, add that chosen card to your hand, fetched up from below, and draw one card from the Tower."},
 {"mechanical_expression":"One card is sent down into Sheol ahead of you, and the descent pays for itself: the weightiest word lying there, with LORE four or more, is fetched up from below into the hand, and one more card is drawn from the Tower.",
  "semantic_anchor":"fetched up from below",
  "semantic_evidence":["Put one card from your hand into Sheol","choose one card in Sheol that has LORE four or more","add that chosen card to your hand and draw one card from the Tower"],
  "ability_text":"Put one card from your hand into Sheol. Then choose one card in Sheol that has LORE four or more, add that chosen card to your hand and draw one card from the Tower.",
  "rules_terms":["card","hand","Sheol","LORE","Tower","put","choose","add","draw"],
  "rules_actions":["put","choose","add","draw"],
  "clarity":cl(targets=["one card in Sheol that has LORE four or more","your hand"],zones=["hand","Sheol","Tower"],quantities=["one card","one card"],outcomes=["Put one card from your hand into Sheol","add that chosen card to your hand and draw one card from the Tower"]),
  "rarity_budget":budget(2,3,1,0,2, why=["the hand, Sheol and the Tower","one placement, one search of Sheol, one add and one draw","Sheol must already hold a card of LORE four or more for the descent to be worth making","no other player is touched","a heavy card fetched out of Sheol and one card drawn, against one card sent down"]) })
META["DESCEND"] = {"gloss":"To come down from a higher place to a lower","weight":3,"weight_rationale":"the LORD coming down is how the era's two great judgments open, at Babel and again over Sodom, and the same verb carries the descent from heaven in John - thematic vocabulary with real teaching, while the named events the era turns on are Babel and Sodom rather than the verb, so DESCEND stays at 3 and prints UNCOMMON",
 "art_prompt":"Seen from far above, the flat roofs and narrow brick lanes of a city dropping away below, one empty street at the foot of a long outer stair, swallows turning in the air between, no people, "+S("storm"),
 "stats":{"lore":4,"context":5,"complexity":3},
 "stats_rationale":{"lore":"the printed verses have the LORD come down to see what the builders have made and the Son of man come down out of heaven - in this era a descent is God arriving to judge or to save, and both printed verses say so","context":"yarad occurs 380 times in the Hebrew Bible; katabaino occurs 81 times in the New Testament; total 461","complexity":"yarad reports direction rather than dignity, so the same verb takes a bucket down a well, a man down to Egypt and the LORD down to Babel, and Hebrew keeps using it for travel toward the coast or the south where English would never say down at all"},
 "ot_verse":{"ref":"Genesis 11:5","snippet":"And the LORD came down to see the city and the tower, which the children of men builded"},"nt_verse":{"ref":"John 3:13","snippet":"no man hath ascended up to heaven, but he that came down from heaven"},
 "greek":{"text":"καταβαίνω","translit":"katabaino"},"hebrew":{"text":"יָרַד","translit":"yarad"},
 "ot_refs":"Gen 11:5 • Gen 11:7 • Gen 18:21","nt_refs":"John 3:13 • John 6:38 • 1 Thess 4:16",
 "trivia":["The builders say let us go up; the very next verse says the LORD came down - the tower meant to reach heaven still has to be stooped to.","Genesis uses the same coming down before Sodom, where God says I will go down now, and see, as though judgment required an inspection first.","Hebrew direction is fixed to the land rather than the compass, so one always goes down to Egypt and up to Jerusalem, however the road actually runs."]}

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

TYPES = {"EARTH":"NOUN","STONE":"NOUN","CITY":"NOUN","NAME":"NOUN","DESCEND":"VERB"}
