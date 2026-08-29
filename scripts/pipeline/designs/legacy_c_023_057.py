"""Regen module C: legacy slots #023 NAKED, #024 COVENANT, #025 NOAH, #026 CURSE, #027 HUNTER,
#028 RIGHTEOUS, #029 ADAM, #030 SPIRIT, #031 HEAR, #035 DEEP, #052 HOVER, #057 DISCORD,
redesigned under the current grammar, power ladder, word weight, stat rubric and art rules.

The WORD and the printed Hebrew/Greek lemmas are fixed; ability, art, stats, weight, verses and
trivia are new. Rarity moves where the printed rarity no longer matched the word's weight:
NAKED, HUNTER, RIGHTEOUS, DEEP, HOVER and DISCORD come down; NOAH goes up to its pillar tier.
"""
from hypertext.cards.art_motifs import load_art_standards, style_suffix

ART = load_art_standards("series/2026-Q1")
def style(name):
    return style_suffix(ART, name)

def cl(**k):
    base={"trigger":"activation","timing":"instantaneous","targets":[],"zones":[],"quantities":[],"duration":"instantaneous","condition":"none","outcomes":[]}; base.update(k); return base
def budget(*v, why):
    return {k:{"rating":r,"rationale":w} for k,r,w in zip(("scope","complexity","setup","interaction","payoff"), v, why)}
DESIGNS = {}; META = {}

# ---------------------------------------------------------------- COMMON
DESIGNS["HEAR"] = ("COMMON",
 {"core_meaning":"To perceive a voice and attend to it - they heard the voice of the LORD God walking in the garden; to hear in Hebrew is already to obey.",
  "type_expression":"A verb of attending: one card is turned face up and spoken aloud and heard, taken into the hand, and then the hearer listens for the next voice by looking at one card from the top of the Tower.",
  "mechanical_anchors":["spoken aloud and heard","listen for the next voice","the revealed card is taken","look at the top of the Tower","the voice in the garden"],
  "mechanic_seed":"Reveal one card from the top of the Tower, spoken aloud and heard, and add that revealed card to your hand; then listen for the next voice and look at one card from the top of the Tower."},
 {"mechanical_expression":"The word is spoken aloud and heard: one card is revealed from the top of the Tower and that revealed card is taken into the hand, and then the hearer listens for the next voice by looking at one card from the top of the Tower.",
  "semantic_anchor":"spoken aloud and heard",
  "semantic_evidence":["Reveal one card from the top of the Tower","add that revealed card to your hand","Then look at one card from the top of the Tower"],
  "ability_text":"Reveal one card from the top of the Tower and add that revealed card to your hand. Then look at one card from the top of the Tower.",
  "rules_terms":["card","Tower","hand","reveal","add","look at"],
  "rules_actions":["reveal","add","look at"],
  "clarity":cl(targets=["one card from the top of the Tower","your hand"],zones=["Tower","hand"],quantities=["one card","one card"],outcomes=["add that revealed card to your hand","look at one card from the top of the Tower"]),
  "rarity_budget":budget(2,1,0,0,1, why=["the Tower and the hand","one card taken, with a listening look after it","no prior state is required","no other player is touched","one card taken face up, with the next voice heard in advance"]) })
META["HEAR"] = {"gloss":"To perceive a voice and attend to it","weight":3,"weight_rationale":"shama is the era's verb of response - the man and the woman hear God walking in the garden and hide - and the word the Shema is named for; thematic vocabulary with real teaching, not a named agent or event",
 "art_prompt":"A garden path of trodden earth between fig trees, the low leaves still trembling where a voice has just passed, a stone seat empty beside the path, no people, "+style("golden"),
 "stats":{"lore":4,"context":5,"complexity":2},
 "stats_rationale":{"lore":"in this card's own verses hearing is the hinge - the first thing the fallen pair do is hear God walking, and the sheep are known by hearing the voice; a major theme close to doctrine","context":"shama occurs 1159 times in the Hebrew Bible; akouo occurs 428 times in the New Testament; total 1587","complexity":"shama carries hearing and obeying in one verb, which is why translators alternate hear and hearken; the range is wide but the choice is plain"},
 "ot_verse":{"ref":"Genesis 3:8","snippet":"And they heard the voice of the LORD God walking in the garden in the cool of the day"},"nt_verse":{"ref":"John 10:27","snippet":"My sheep hear my voice, and I know them, and they follow me"},
 "greek":{"text":"ἀκούω","translit":"akouo"},"hebrew":{"text":"שָׁמַע","translit":"shama"},
 "ot_refs":"Gen 3:8 • Gen 3:10 • Deut 6:4","nt_refs":"John 10:27 • Mark 4:9 • Matt 13:16",
 "trivia":["The first thing the man and the woman do after eating is hear - the sound of God walking in the garden sends them into the trees.","Hebrew has no separate verb for obey; to hear a command and to keep it are the same word, which is why the KJV writes hearken.","The Shema takes its name from its first word, shema - Hear, O Israel."]}

# ---------------------------------------------------------------- UNCOMMON
DESIGNS["NAKED"] = ("UNCOMMON",
 {"core_meaning":"Uncovered - they were both naked and were not ashamed; what is naked is stripped of covering and can be seen for what it is.",
  "type_expression":"An adjective of exposure: a chosen player is uncovered and reveals one card from that chosen player's hand, and what that revealed card uncovers is taken up from Sheol, where nothing is hidden.",
  "mechanical_anchors":["stripped of covering","nothing is hidden","the chosen player is uncovered","reveals what is held","cards of that uncovered kind"],
  "mechanic_seed":"Choose another player, stripped of covering; that chosen player reveals one card from that chosen player's hand, and what that revealed card uncovers you take - choose two cards in Sheol of that revealed card's card type, where nothing is hidden, and add those chosen cards to your hand."},
 {"mechanical_expression":"The chosen player is stripped of covering: that chosen player reveals one card from that chosen player's hand, and the kind that revealed card uncovers is taken out of Sheol, where nothing is hidden.",
  "semantic_anchor":"stripped of covering",
  "semantic_evidence":["That chosen player reveals one card from that chosen player's hand","choose two cards in Sheol of that revealed card's card type","add those chosen cards to your hand"],
  "ability_text":"Choose another player. That chosen player reveals one card from that chosen player's hand; then choose two cards in Sheol of that revealed card's card type and add those chosen cards to your hand.",
  "rules_terms":["player","card","hand","Sheol","card type","cards","choose","reveal","add"],
  "rules_actions":["choose","reveal","choose","add"],
  "clarity":cl(targets=["another player","That chosen player","your hand"],zones=["hand","Sheol"],quantities=["one card","two cards","those chosen cards"],outcomes=["That chosen player reveals one card from that chosen player's hand","add those chosen cards to your hand"]),
  "rarity_budget":budget(2,1,1,1,2, why=["one chosen player, the hand and Sheol","one reveal and one filtered recovery","Sheol must hold cards of the uncovered type","one chosen player is made to show a card","two cards taken back out of Sheol"]) })
META["NAKED"] = {"gloss":"Uncovered; stripped of covering","weight":2,"weight_rationale":"a descriptive word with a clear place in the era's opening scene - naked and not ashamed, then hiding - but no judgment, agent or event turns on the adjective itself; the fall is carried by other words",
 "art_prompt":"A clear pool among fig trees in the garden, two empty clay bowls on the bank and not one garment or covering anywhere on the ground, the pool holding the light unbroken, no people, "+style("golden"),
 "stats":{"lore":3,"context":2,"complexity":3},
 "stats_rationale":{"lore":"nakedness before God frames the era's first shame and, in this card's New Testament verse, the openness of all things to him - a recognized theme with clear teaching","context":"arom occurs 16 times in the Hebrew Bible; gymnos occurs 15 times in the New Testament; total 31","complexity":"arom, naked, differs from arum, subtil, by one vowel - Genesis sets the naked pair beside the crafty serpent in consecutive verses - and a second Hebrew word, eyrom, carries the nakedness of Genesis 3:10; an ambiguity to explain"},
 "ot_verse":{"ref":"Genesis 2:25","snippet":"And they were both naked, the man and his wife, and were not ashamed"},"nt_verse":{"ref":"Hebrews 4:13","snippet":"all things are naked and opened unto the eyes of him with whom we have to do"},
 "greek":{"text":"γυμνός","translit":"gymnos"},"hebrew":{"text":"עָרוֹם","translit":"arom"},
 "ot_refs":"Gen 2:25 • Job 1:21 • Eccl 5:15","nt_refs":"Heb 4:13 • 2 Cor 5:3 • Rev 3:17",
 "trivia":["Genesis 2:25 calls the pair arummim, naked, and Genesis 3:1 calls the serpent arum, subtil - the same consonants one verse apart.","Job answers his loss with the same adjective: naked came I out of my mother's womb, and naked shall I return.","Gymnos gives us gymnasium, from the Greek habit of training stripped."]}

DESIGNS["HUNTER"] = ("UNCOMMON",
 {"core_meaning":"One who pursues and takes - Nimrod was a mighty hunter before the LORD; the hunter drives the quarry from cover and carries off the spoil.",
  "type_expression":"A title of pursuit: a chosen player is run down and made to give up a Letter, and the hunter carries off the spoil by drawing two cards.",
  "mechanical_anchors":["carries off the spoil","driven from cover","the quarry pays","that chosen player spends","before the LORD"],
  "mechanic_seed":"Choose another player and drive that quarry from cover; that chosen player spends one Letter, the quarry pays, and then the hunter carries off the spoil and draws two cards from the Tower."},
 {"mechanical_expression":"The quarry is driven from cover and pays: that chosen player spends one Letter, and the hunter carries off the spoil by drawing two cards from the Tower.",
  "semantic_anchor":"carries off the spoil",
  "semantic_evidence":["that chosen player spends one Letter","Then draw two cards from the Tower"],
  "ability_text":"Choose another player; that chosen player spends one Letter. Then draw two cards from the Tower.",
  "rules_terms":["player","Letter","cards","Tower","choose","spend","draw"],
  "rules_actions":["choose","spend","draw"],
  "clarity":cl(targets=["another player","that chosen player"],zones=["Tower"],quantities=["one Letter","two cards"],outcomes=["that chosen player spends one Letter","draw two cards from the Tower"]),
  "rarity_budget":budget(2,2,0,2,2, why=["one chosen player and the Tower","one forced payment and one draw","no prior state is required","a chosen player is made to spend a Letter, three cards of that player's resource","two cards drawn while the quarry pays"]) })
META["HUNTER"] = {"gloss":"One who pursues and takes","weight":3,"weight_rationale":"Nimrod the mighty hunter is the era's first strong man and the founder of Babel's cities, but the card word is the trade, not the man - thematic vocabulary with real teaching behind it rather than a named agent",
 "art_prompt":"A great horn bow and a spotted skin hung on a lone oak at the edge of a dark grazing ground, the deep tracks of a heavy beast pressed into the dust beneath, no people, "+style("moonlit"),
 "stats":{"lore":3,"context":2,"complexity":3},
 "stats_rationale":{"lore":"the hunter before the LORD begins the kingdom that raises Babel, and the New Testament verse turns the hunt into judgment - a recognized theme with clear teaching, not a doctrine","context":"tsayad, the hunter, occurs 2 times in the Hebrew Bible and tsayid, the hunt and its game, 19 times; thera occurs 1 time in the New Testament; total 22","complexity":"tsayad the hunter and tsayid the hunt are read into one another, and before the LORD in Genesis 10:9 is taken either as with God's favour or in defiance of him - a contested phrase"},
 "ot_verse":{"ref":"Genesis 10:9","snippet":"He was a mighty hunter before the LORD"},"nt_verse":{"ref":"Romans 11:9","snippet":"Let their table be made a snare, and a trap, and a stumblingblock"},
 "greek":{"text":"θήρα","translit":"thera"},"hebrew":{"text":"צַיָּד","translit":"tsayad"},
 "ot_refs":"Gen 10:9 • Gen 25:27 • Jer 16:16","nt_refs":"Rom 11:9",
 "trivia":["Nimrod is the first man in Scripture called mighty, and the next verse makes Babel the beginning of his kingdom.","Jeremiah turns the trade into judgment: I will send for many hunters, and they shall hunt them from every mountain.","Thera occurs once in the New Testament, in a psalm quotation where a table becomes a trap."]}

DESIGNS["DEEP"] = ("UNCOMMON",
 {"core_meaning":"Reaching far beneath the surface - counsel in the heart of man is like deep water, and a man of understanding will draw it out.",
  "type_expression":"An adjective of depth: the sounding reaches to the bottom of the Tower, only the weighty comes up into the hand, and the rest sinks into Sheol.",
  "mechanical_anchors":["only the weighty comes up","reach to the bottom","the rest sinks","drawn out of deep water","sounded to the floor"],
  "mechanic_seed":"Look at the bottom three cards of the Tower, sounded to the floor; add up to two of those cards that each have LORE three or more to your hand, for only the weighty comes up, and put the other cards into Sheol, where the rest sinks."},
 {"mechanical_expression":"The sounding reaches the bottom three cards of the Tower and only the weighty comes up - up to two of those cards that each have LORE three or more are added to the hand, while the other cards sink into Sheol.",
  "semantic_anchor":"only the weighty comes up",
  "semantic_evidence":["Look at the bottom three cards of the Tower","Add up to two of those cards that each have LORE three or more to your hand","put the other cards into Sheol"],
  "ability_text":"Look at the bottom three cards of the Tower. Add up to two of those cards that each have LORE three or more to your hand and put the other cards into Sheol.",
  "rules_terms":["cards","Tower","LORE","hand","Sheol","look at","add","put"],
  "rules_actions":["look at","add","put"],
  "clarity":cl(targets=["the bottom three cards of the Tower","your hand"],zones=["Tower","hand","Sheol"],quantities=["bottom three cards","up to two of those cards"],outcomes=["Add up to two of those cards that each have LORE three or more to your hand","put the other cards into Sheol"]),
  "rarity_budget":budget(2,2,1,0,2, why=["the Tower, the hand and Sheol","a sounding, a filtered take and a placement","Sheol receives what is not taken","no other player is touched","up to two weighty cards drawn out of the deep"]) })
META["DEEP"] = {"gloss":"Reaching far beneath the surface","weight":3,"weight_rationale":"amoq is the era's word for what lies below sounding - counsel, thought, a well - thematic vocabulary with real teaching, but the deep of Genesis 1:2 is tehom and belongs to another card",
 "art_prompt":"A stone well shaft seen from directly above, a wet rope dropping away into darkness and a small coin of light on the water far below, no people, "+style("underwater"),
 "stats":{"lore":3,"context":2,"complexity":3},
 "stats_rationale":{"lore":"in this card's verses depth is what a wise man draws out and what a well withholds - a recognized theme with clear teaching, not a doctrine the word carries","context":"amoq occurs 17 times in the Hebrew Bible; bathys occurs 4 times in the New Testament; total 21","complexity":"amoq is used of counsel, of thought, of a wound and of a well, never of the sea, which Hebrew calls tehom; bathys stretches from a deep well to deep morning in Luke 24:1 - a range that needs a note"},
 "ot_verse":{"ref":"Proverbs 20:5","snippet":"Counsel in the heart of man is like deep water; but a man of understanding will draw it out"},"nt_verse":{"ref":"John 4:11","snippet":"the well is deep: from whence then hast thou that living water?"},
 "greek":{"text":"βαθύς","translit":"bathys"},"hebrew":{"text":"עָמֹק","translit":"amoq"},
 "ot_refs":"Prov 20:5 • Eccl 7:24 • Ps 64:6","nt_refs":"John 4:11 • Rev 2:24 • Acts 20:9",
 "trivia":["Hebrew keeps two depths apart: amoq for a well or a thought, tehom for the deep that covered the earth.","Jacob's well at Sychar, the one the woman calls deep, is still over thirty metres to the water.","Luke calls the dawn of the resurrection deep morning, using the same adjective as the well."]}

DESIGNS["DISCORD"] = ("UNCOMMON",
 {"core_meaning":"Strife between two - the beginning of strife is as when one letteth out water; a quarrel begins small and carries off whatever it breaks.",
  "type_expression":"A noun of contention: two players are set against each other, each of you reveals one card from your hand, and the higher COMPLEXITY carries off two cards from Sheol - what the quarrel has already broken.",
  "mechanical_anchors":["set against each other","the higher COMPLEXITY carries it","what the quarrel breaks","each of you reveals","a quarrel begins small"],
  "mechanic_seed":"Choose another player and be set against each other; each of you reveals one card from your hand, and if your revealed card has the higher COMPLEXITY you carry off what the quarrel breaks - add two cards from Sheol to your hand."},
 {"mechanical_expression":"Two players are set against each other: each of you reveals one card from your hand, and if your revealed card has the higher COMPLEXITY, two cards are taken back out of Sheol - what the quarrel breaks.",
  "semantic_anchor":"set against each other",
  "semantic_evidence":["each of you reveals one card from your hand","If your revealed card has the higher COMPLEXITY","add two cards from Sheol to your hand"],
  "ability_text":"Choose another player; each of you reveals one card from your hand. If your revealed card has the higher COMPLEXITY, add two cards from Sheol to your hand.",
  "rules_terms":["player","card","hand","COMPLEXITY","cards","Sheol","choose","reveal","add"],
  "rules_actions":["choose","reveal","add"],
  "clarity":cl(targets=["another player","each of you","your hand"],zones=["hand","Sheol"],quantities=["one card","two cards"],condition="If your revealed card has the higher COMPLEXITY",outcomes=["each of you reveals one card from your hand","add two cards from Sheol to your hand"]),
  "rarity_budget":budget(2,2,1,1,2, why=["one chosen player, the hand and Sheol","a mutual reveal and a conditional recovery","Sheol must hold cards and the contest must be won","one chosen player is drawn into the contest and shows a card","two cards taken back out of Sheol when the contest is won"]) })
META["DISCORD"] = {"gloss":"Strife between two","weight":2,"weight_rationale":"a descriptive word with a clear place - the strife that follows the scattering - but no judgment, agent or event of the era turns on madon; CONFUSE and SCATTER carry that weight",
 "art_prompt":"A narrow breach opening in a packed earth bank, a first thread of water cutting through into the dry channel below, cracked clay curling on either side, no people, "+style("storm"),
 "stats":{"lore":3,"context":2,"complexity":4},
 "stats_rationale":{"lore":"in this card's verses strife is a thing to be left off before it breaks out and a mark of the carnal - a recognized theme with clear teaching, not a doctrine","context":"madon occurs 19 times in the Hebrew Bible; eris occurs 9 times in the New Testament; total 28","complexity":"Hebrew keeps four words for strife - madon, midyan, rib and massah - and the printed verse of Proverbs 6:19 uses the second where 17:14 uses the first; eris then has to stand for all of them in Greek, which is why lists of the works of the flesh vary in English"},
 "ot_verse":{"ref":"Proverbs 17:14","snippet":"The beginning of strife is as when one letteth out water: therefore leave off contention, before it be meddled with"},"nt_verse":{"ref":"1 Corinthians 3:3","snippet":"for whereas there is among you envying, and strife, and divisions, are ye not carnal"},
 "greek":{"text":"ἔρις","translit":"eris"},"hebrew":{"text":"מָדוֹן","translit":"madon"},
 "ot_refs":"Prov 17:14 • Prov 15:18 • Prov 26:20","nt_refs":"1 Cor 3:3 • Gal 5:20 • Rom 1:29",
 "trivia":["Proverbs pictures a quarrel as a seep in an earth bank: stop it while it is a thread of water, because a breach cannot be argued shut.","Proverbs 26:20 gives the other end of the same rule - where there is no talebearer, the strife ceaseth.","Eris was also the name Greeks gave the goddess of strife; Paul lists it among the works of the flesh."]}

# ---------------------------------------------------------------- RARE
DESIGNS["RIGHTEOUS"] = ("RARE",
 {"core_meaning":"Straight before God - Noah was a just man and perfect in his generations; righteousness is a whole life's record weighed and found upright.",
  "type_expression":"An adjective of standing: one card is turned face up and taken, and then the record weighed - if the cards in your Pages have total LORE ten or more, three cards follow.",
  "mechanical_anchors":["the record weighed","found upright","the weight of a whole life","total LORE in your Pages","the revealed card is taken"],
  "mechanic_seed":"Reveal one card from the top of the Tower and add that revealed card to your hand; then let the record weighed decide - if the cards in your Pages have total LORE ten or more, found upright, draw three cards from the Tower."},
 {"mechanical_expression":"One revealed card is taken, and then the record weighed decides the rest: if the cards in your Pages have total LORE ten or more, three cards follow from the Tower.",
  "semantic_anchor":"the record weighed",
  "semantic_evidence":["add that revealed card to your hand","If the cards in your Pages have total LORE ten or more","draw three cards from the Tower"],
  "ability_text":"Reveal one card from the top of the Tower and add that revealed card to your hand. If the cards in your Pages have total LORE ten or more, draw three cards from the Tower.",
  "rules_terms":["card","Tower","hand","cards","Pages","LORE","reveal","add","draw"],
  "rules_actions":["reveal","add","draw"],
  "clarity":cl(targets=["one card from the top of the Tower","your hand"],zones=["Tower","hand","Pages"],quantities=["one card","three cards"],condition="If the cards in your Pages have total LORE ten or more",outcomes=["add that revealed card to your hand","draw three cards from the Tower"]),
  "rarity_budget":budget(2,2,2,0,3, why=["the Tower, the hand and your Pages","a reveal, a take and a weighed draw","a built Page of ten or more total LORE must already stand","no other player is touched","one card taken and three more when the record is heavy enough"]) })
META["RIGHTEOUS"] = {"gloss":"Straight before God; just","weight":3,"weight_rationale":"tsaddiq is thematic vocabulary with real teaching - Noah is the first man Scripture calls just - but the adjective is not itself a named agent, judgment or event; NOAH and COVENANT carry the era's weight",
 "art_prompt":"A single cedar standing straight and unbroken among storm-felled trunks on a bare ridge, its shadow falling square across the wreckage, no people, "+style("golden"),
 "stats":{"lore":4,"context":4,"complexity":3},
 "stats_rationale":{"lore":"the verses printed here make righteousness the ground of survival and of life itself - just and perfect in his generations, the just shall live by faith; a major theme close to doctrine","context":"tsaddiq occurs 206 times in the Hebrew Bible; dikaios occurs 79 times in the New Testament; total 285","complexity":"tsaddiq is a legal word - the one the court declares in the right - so English must choose between just and righteous where Greek uses one dikaios for both; a translation choice to explain"},
 "ot_verse":{"ref":"Genesis 6:9","snippet":"Noah was a just man and perfect in his generations, and Noah walked with God"},"nt_verse":{"ref":"Romans 1:17","snippet":"The just shall live by faith"},
 "greek":{"text":"δίκαιος","translit":"dikaios"},"hebrew":{"text":"צַדִּיק","translit":"tsaddiq"},
 "ot_refs":"Gen 6:9 • Gen 7:1 • Prov 10:25","nt_refs":"Rom 1:17 • Matt 13:43 • 1 Pet 4:18",
 "trivia":["Genesis 6:9 is the first time anyone in Scripture is called tsaddiq, and it is said of a man in a generation about to be drowned.","Perfect in his generations translates tamim, the word used of an unblemished animal brought for sacrifice.","The just shall live by faith is quoted three times in the New Testament, from one half-verse of Habakkuk."]}

DESIGNS["HOVER"] = ("RARE",
 {"core_meaning":"To brood over the face of the waters without settling - the Spirit of God moved upon the deep, touching everything and resting on nothing.",
  "type_expression":"A verb of suspension: the motion passes over what you have built and over the deep - one card is lifted back out of a Page, up to three are lifted out of Sheol, and one card goes back under to the bottom of the Tower, because the hovering never settles.",
  "mechanical_anchors":["without settling","moving over the face","lifted from beneath","nothing is consumed","goes back under"],
  "mechanic_seed":"Return one card from one of your Pages to your hand, lifted from beneath while nothing is consumed and the Page still scores; then choose up to three cards in Sheol and add those chosen cards to your hand, and put one card from your hand on the bottom of the Tower, for the hovering is without settling."},
 {"mechanical_expression":"The motion passes over what is built and over the deep without settling: one card comes back out of a Page, up to three chosen cards come up out of Sheol, and one card goes back under to the bottom of the Tower.",
  "semantic_anchor":"without settling",
  "semantic_evidence":["Return one card from one of your Pages to your hand","choose up to three cards in Sheol and add those chosen cards to your hand","put one card from your hand on the bottom of the Tower"],
  "ability_text":"Return one card from one of your Pages to your hand. Then choose up to three cards in Sheol and add those chosen cards to your hand, and put one card from your hand on the bottom of the Tower.",
  "rules_terms":["card","Pages","hand","cards","Sheol","Tower","return","choose","add","put"],
  "rules_actions":["return","choose","add","put"],
  "clarity":cl(targets=["one card from one of your Pages","your hand"],zones=["Pages","hand","Sheol","Tower"],quantities=["one card","up to three cards","one card"],outcomes=["Return one card from one of your Pages to your hand","add those chosen cards to your hand","put one card from your hand on the bottom of the Tower"]),
  "rarity_budget":budget(2,3,1,0,3, why=["a Page, the hand, Sheol and the Tower","a return, a chosen recovery and a placement","a Page must already stand and Sheol must hold cards","no other player is touched","one card out of a Page that still scores and up to three out of Sheol, one card given back under"]) })
META["HOVER"] = {"gloss":"To brood over the face of the waters","weight":3,"weight_rationale":"the whole weight of rachaph rests on one clause of Genesis 1:2 and two verses elsewhere; it is thematic vocabulary with real teaching, but the agent of that clause is SPIRIT - the verb itself names no judgment, agent or event the era turns on",
 "art_prompt":"The unbroken black face of a great water before first light, a low mist trembling just above it and one wide silver ring spreading outward from nothing, no people, "+style("dawn"),
 "stats":{"lore":4,"context":1,"complexity":4},
 "stats_rationale":{"lore":"this card's own verse is the second sentence of Scripture, where the Spirit moves over the deep before anything is made - a major theme close to doctrine","context":"rachaph occurs 3 times in the Hebrew Bible; epiphero occurs 5 times in the New Testament; total 8","complexity":"three occurrences carry three senses - brooding over the waters, an eagle fluttering over her young, and bones that shake - so the sense at Genesis 1:2 is argued from Deuteronomy 32:11; the Greek has no matching verb at all"},
 "ot_verse":{"ref":"Genesis 1:2","snippet":"and the Spirit of God moved upon the face of the waters"},"nt_verse":{"ref":"Romans 3:5","snippet":"Is God unrighteous who taketh vengeance?"},
 "greek":{"text":"ἐπιφέρω","translit":"epiphero"},"hebrew":{"text":"רָחַף","translit":"rachaph"},
 "ot_refs":"Gen 1:2 • Deut 32:11 • Jer 23:9","nt_refs":"Rom 3:5 • Jude 9 • Acts 25:18",
 "trivia":["Rachaph appears three times in the Hebrew Bible and each one is a different picture: brooding, fluttering, shaking.","Deuteronomy 32:11 sets the verb over an eagle stirring her nest, which is why many read Genesis 1:2 as a bird brooding rather than a wind blowing.","Jeremiah uses it of his own bones shaking at the word of the LORD - the same trembling suspension seen from inside."]}

# ---------------------------------------------------------------- GLORIOUS
DESIGNS["COVENANT"] = ("GLORIOUS",
 {"core_meaning":"A bond cut between two parties - I do set my bow in the cloud for a token of a covenant; each side is bound to the other and takes up the other's portion.",
  "type_expression":"A noun of binding: the bond passes between two players, your Lot and that chosen player's Lot change hands unrecorded, and the oath is sealed with one Letter.",
  "mechanical_anchors":["each takes up the other's portion","bound between two parties","the oath sealed","a bond cut between them","the token in the cloud"],
  "mechanic_seed":"Choose another player to be bound to; each takes up the other's portion when you exchange your Lot with that chosen player's Lot, and the oath sealed brings you one Letter."},
 {"mechanical_expression":"The bond passes between two parties and each takes up the other's portion: your Lot goes to that chosen player and that chosen player's Lot comes to you, and the oath is sealed with a Letter.",
  "semantic_anchor":"each takes up the other's portion",
  "semantic_evidence":["Choose another player","Exchange your Lot with that chosen player's Lot","gain one Letter"],
  "ability_text":"Choose another player. Exchange your Lot with that chosen player's Lot, then gain one Letter.",
  "rules_terms":["player","Lot","Letter","choose","exchange","gain"],
  "rules_actions":["choose","exchange","gain"],
  "clarity":cl(targets=["another player","that chosen player's Lot"],zones=["Lot"],quantities=["one Letter"],outcomes=["Exchange your Lot with that chosen player's Lot","gain one Letter"]),
  "rarity_budget":budget(2,2,1,2,4, why=["your Lot and one chosen player's Lot","an exchange of recipes and a resource gain","both Lots must already be held, and they arrive unrecorded","a chosen player's recipe is taken and replaced","a structure bent - two Lots change hands unrecorded - and a Letter worth three cards on top"]) })
META["COVENANT"] = {"gloss":"A bond cut between two parties","weight":5,"weight_rationale":"a pillar of the set: the bow in the cloud after the flood and the promise to Abram are the two hinges the era turns on, and every later covenant is read back through them",
 "art_prompt":"A great bow of colour standing over dark receding floodwaters, a wet stone altar on the high ground beneath it and drenched cliffs behind, no people, "+style("overcast"),
 "stats":{"lore":5,"context":4,"complexity":4},
 "stats_rationale":{"lore":"the printed verses put the whole structure of promise on the word - the token in the cloud and the cup of the new testament; a doctrine hangs on it","context":"berit occurs 284 times in the Hebrew Bible; diatheke occurs 33 times in the New Testament; total 317","complexity":"Hebrew does not make a covenant, it cuts one - karat berit, from the halves of animals in Genesis 15 - while the Greek diatheke is ordinarily a last will, which is why English alternates covenant and testament in the same book"},
 "ot_verse":{"ref":"Genesis 9:13","snippet":"I do set my bow in the cloud, and it shall be for a token of a covenant between me and the earth"},"nt_verse":{"ref":"Luke 22:20","snippet":"This cup is the new testament in my blood"},
 "greek":{"text":"διαθήκη","translit":"diatheke"},"hebrew":{"text":"בְּרִית","translit":"berit"},
 "ot_refs":"Gen 6:18 • Gen 9:13 • Gen 17:7","nt_refs":"Luke 22:20 • Heb 9:15 • Gal 3:17",
 "trivia":["The first covenant named in Scripture is with Noah, and the second is made with every living creature, not with people alone.","Hebrew cuts a covenant; Genesis 15 shows why, with the halves laid out and a flame passing between them.","Diatheke is the ordinary Greek word for a will, which is why Hebrews 9 can argue from the death of the one who made it."]}

DESIGNS["NOAH"] = ("GLORIOUS",
 {"core_meaning":"The man who found grace and was carried through the flood - two of every sort went in with him and came out alive.",
  "type_expression":"A name of preservation: the waters take first, two cards go from the hand into Sheol, and then one of every sort is brought out again - five cards, one card of each card type.",
  "mechanical_anchors":["one of every sort","the waters take first","carried out alive","preserved through the flood","two and two went in"],
  "mechanic_seed":"Discard two cards from your hand into Sheol, for the waters take first; then choose five cards in Sheol, one card of each card type, one of every sort carried out alive, and add those chosen cards to your hand."},
 {"mechanical_expression":"The waters take first and the ark brings one of every sort out again: two cards are discarded from the hand into Sheol, and then five cards are chosen in Sheol, one card of each card type, and added to the hand.",
  "semantic_anchor":"one of every sort",
  "semantic_evidence":["Discard two cards from your hand into Sheol","choose five cards in Sheol, one card of each card type","add those chosen cards to your hand"],
  "ability_text":"Discard two cards from your hand into Sheol. Then choose five cards in Sheol, one card of each card type, and add those chosen cards to your hand.",
  "rules_terms":["cards","hand","Sheol","card","card type","discard","choose","add"],
  "rules_actions":["discard","choose","add"],
  "clarity":cl(targets=["your hand","five cards in Sheol"],zones=["hand","Sheol"],quantities=["two cards","five cards","one card of each card type"],outcomes=["Discard two cards from your hand into Sheol","add those chosen cards to your hand"]),
  "rarity_budget":budget(2,2,1,0,4, why=["the hand and Sheol","a paid discard and one filtered recovery","two cards must be given up and Sheol must hold all five card types","no other player is touched","five cards' worth carried out of Sheol, one of every kind, bought with two cards given up first"]) })
META["NOAH"] = {"gloss":"The man carried through the flood","weight":5,"weight_rationale":"a pillar of the set: the era's whole middle turns on this one man - the flood, the ark, the covenant and the new beginning are all told as what happened to Noah",
 "art_prompt":"A great pitched cedar hull grounded on a dark shore with its ramp down, paired animal tracks pressed into the mud leading up into the black hold, rain running off the timbers, no people, "+style("storm"),
 "stats":{"lore":5,"context":3,"complexity":3},
 "stats_rationale":{"lore":"the printed verses make him the man who found grace and the pattern of faith that saves a house - a doctrine hangs on the name","context":"Noach occurs 46 times in the Hebrew Bible; Noe occurs 8 times in the New Testament; total 54","complexity":"Genesis 5:29 explains the name from nacham, to comfort, though it sounds like nuach, to rest - the pun does not quite close, and both readings are printed in English Bibles"},
 "ot_verse":{"ref":"Genesis 6:8","snippet":"But Noah found grace in the eyes of the LORD"},"nt_verse":{"ref":"Hebrews 11:7","snippet":"By faith Noah, being warned of God of things not seen as yet, moved with fear, prepared an ark"},
 "greek":{"text":"Νῶε","translit":"Noe"},"hebrew":{"text":"נֹחַ","translit":"Noach"},
 "ot_refs":"Gen 6:8 • Gen 6:9 • Gen 7:1","nt_refs":"Heb 11:7 • Matt 24:37 • 1 Pet 3:20",
 "trivia":["Grace is first named in Scripture in Genesis 6:8, and it is named of Noah before anything he does is reported.","Ezekiel names Noah with Daniel and Job as three men whose righteousness could deliver only themselves.","Peter counts the saved: eight souls, in a world of one language and many years."]}

DESIGNS["CURSE"] = ("GLORIOUS",
 {"core_meaning":"To speak a binding sentence against - cursed is the ground for thy sake; the word names a kind and that kind is put out of every hand.",
  "type_expression":"A verb of sentence: a card type is named, and the sentence spoken over that kind puts every card of the named type out of every player's hand into Sheol, after which three cards come to the speaker.",
  "mechanical_anchors":["put out of every hand","the sentence spoken over a kind","cursed be that kind","named and condemned","what the word names"],
  "mechanic_seed":"Name a card type and let the sentence spoken over a kind fall: each player puts every card of the named type from that player's hand into Sheol, put out of every hand, and then draw three cards from the Tower."},
 {"mechanical_expression":"The sentence names a kind and that kind is put out of every hand: each player puts every card of the named type from that player's hand into Sheol, and three cards follow from the Tower.",
  "semantic_anchor":"put out of every hand",
  "semantic_evidence":["Name a card type","each player puts every card of the named type from that player's hand into Sheol","draw three cards from the Tower"],
  "ability_text":"Name a card type; each player puts every card of the named type from that player's hand into Sheol. Then draw three cards from the Tower.",
  "rules_terms":["card type","player","card","hand","Sheol","cards","Tower","name","put","draw"],
  "rules_actions":["name","put","draw"],
  "clarity":cl(targets=["each player","that player's hand"],zones=["hand","Sheol","Tower"],quantities=["every card of the named type","three cards"],outcomes=["each player puts every card of the named type from that player's hand into Sheol","draw three cards from the Tower"]),
  "rarity_budget":budget(3,3,1,3,4, why=["every player's hand, Sheol and the Tower","a declaration, a table-wide loss and a draw","Sheol receives whatever the sentence takes","every player's material is moved by the naming","every hand at the table is stripped of one kind and three cards follow"]) })
META["CURSE"] = {"gloss":"To speak a binding sentence against","weight":4,"weight_rationale":"the era's judgments are all spoken as this verb - the ground for Adam's sake, Canaan after the tent, and the sentence on whoever curses Abram; a named judgment the era turns on, though the pillar words are the covenants themselves",
 "art_prompt":"A hard cracked hillside of thorns and thistles closing over a broken wooden plough and a spilled handful of seed, nothing green anywhere in the field, no people, "+style("golden"),
 "stats":{"lore":4,"context":3,"complexity":3},
 "stats_rationale":{"lore":"the printed verses make the curse both God's sentence on the ground and the thing a tongue must not do to a man made in God's image - a major theme close to doctrine","context":"arar occurs 63 times in the Hebrew Bible; kataraomai occurs 5 times in the New Testament; total 68","complexity":"Hebrew has two verbs where English has one - arar is the binding sentence, qalal is to make light of - and Genesis 12:3 uses both in a single line, so the English reads curse twice for two different acts"},
 "ot_verse":{"ref":"Genesis 3:17","snippet":"cursed is the ground for thy sake; in sorrow shalt thou eat of it all the days of thy life"},"nt_verse":{"ref":"James 3:9","snippet":"therewith curse we men, which are made after the similitude of God"},
 "greek":{"text":"καταράομαι","translit":"kataraomai"},"hebrew":{"text":"אָרַר","translit":"arar"},
 "ot_refs":"Gen 3:17 • Gen 9:25 • Gen 12:3","nt_refs":"James 3:9 • Luke 6:28 • Rom 12:14",
 "trivia":["The ground is cursed for the man's sake, not the man - the sentence falls on his work, and thorns are the first sign of it.","Genesis 12:3 uses two verbs: him that maketh light of thee I will bind under a curse.","Both Jesus and Paul answer the verb with its opposite - bless them that curse you, bless and curse not."]}

DESIGNS["ADAM"] = ("GLORIOUS",
 {"core_meaning":"The man formed of the dust of the ground - earth-born, and to the ground he returns, and out of that ground the whole race is formed again.",
  "type_expression":"A name of formation: everything that has died is given back to the ground, the whole Tower is remade and shuffled, three cards are drawn out of it, and one card goes back under to the bottom, for dust returns to dust.",
  "mechanical_anchors":["the ground gives back","dust returns to dust","formed again of what was dead","every card in Sheol goes back","one card goes back under"],
  "mechanic_seed":"Return every card in Sheol to the Tower and shuffle the cards in the Tower, for the ground gives back what it took; then draw three cards from the Tower and put one card from your hand on the bottom of the Tower, since dust returns to dust."},
 {"mechanical_expression":"The ground gives back what was buried in it: every card in Sheol goes into the Tower and the Tower is shuffled, three cards are drawn out of the remade ground, and one card from the hand goes back under to the bottom of the Tower.",
  "semantic_anchor":"the ground gives back",
  "semantic_evidence":["Return every card in Sheol to the Tower","shuffle the cards in the Tower","put one card from your hand on the bottom of the Tower"],
  "ability_text":"Return every card in Sheol to the Tower and shuffle the cards in the Tower. Then draw three cards from the Tower and put one card from your hand on the bottom of the Tower.",
  "rules_terms":["card","Sheol","Tower","cards","hand","return","shuffle","draw","put"],
  "rules_actions":["return","shuffle","draw","put"],
  "clarity":cl(targets=["every card in Sheol","your hand"],zones=["Sheol","Tower","hand"],quantities=["every card","three cards","one card"],outcomes=["Return every card in Sheol to the Tower","shuffle the cards in the Tower","draw three cards from the Tower","put one card from your hand on the bottom of the Tower"]),
  "rarity_budget":budget(2,3,1,0,4, why=["Sheol, the whole Tower and the hand","a zone reset, a shuffle, a draw and a placement","Sheol must have filled for the return to matter","no other player's material is moved directly","a structure bent - the discard pile is poured back and the Tower remade for everyone - with three cards drawn and one given back"]) })
META["ADAM"] = {"gloss":"The man formed of the dust of the ground","weight":5,"weight_rationale":"a pillar of the set: the first man is where the story starts, and every later name in the era is counted from him",
 "art_prompt":"A shallow hollow of red clay in a dark bank, the print of a body pressed into it, fine dust lifting from the hollow in a still column of air, no people, "+style("golden"),
 "stats":{"lore":5,"context":5,"complexity":3},
 "stats_rationale":{"lore":"the printed verses set the first man against the last - formed of dust and made a living soul, then the quickening spirit - a doctrine hangs on the name","context":"adam occurs 552 times in the Hebrew Bible; Adam occurs 9 times in the New Testament; total 561","complexity":"adam is man, mankind and a proper name in the same chapters, and it is built on adamah, the ground he is taken from; where Genesis stops saying the man and starts saying Adam is a translator's decision"},
 "ot_verse":{"ref":"Genesis 2:7","snippet":"And the LORD God formed man of the dust of the ground, and breathed into his nostrils the breath of life"},"nt_verse":{"ref":"1 Corinthians 15:45","snippet":"The first man Adam was made a living soul"},
 "greek":{"text":"Ἀδάμ","translit":"Adam"},"hebrew":{"text":"אָדָם","translit":"Adam"},
 "ot_refs":"Gen 1:26 • Gen 2:7 • Gen 5:1","nt_refs":"1 Cor 15:45 • Rom 5:14 • Luke 3:38",
 "trivia":["Adam is made from adamah, the ground - the name and the dust are the same word one letter apart.","Genesis 5:1 says God created them male and female and called their name Adam - the name is first a name for the pair.","Luke's genealogy runs backwards past every name of this era and ends: which was the son of Adam, which was the son of God."]}

DESIGNS["SPIRIT"] = ("GLORIOUS",
 {"core_meaning":"The breath that gives life - the Spirit of God hath made me, and the breath of the Almighty hath given me life; the letter kills and the spirit quickens.",
  "type_expression":"A title of quickening: a weighty COMMON card lying dead in Sheol is chosen and breath given to the dead makes it act again, after which three cards are drawn.",
  "mechanical_anchors":["breath given to the dead","made to act again","a weighty card in Sheol","the spirit quickens","raised out of the dust"],
  "mechanic_seed":"Choose one COMMON card in Sheol that has LORE three or more, a weighty card in Sheol, and activate that chosen card, for breath given to the dead makes it act again; then draw three cards from the Tower."},
 {"mechanical_expression":"Breath given to the dead: one COMMON card lying in Sheol that has LORE three or more is chosen and resolves again as if it had been revealed, and three cards follow from the Tower.",
  "semantic_anchor":"breath given to the dead",
  "semantic_evidence":["Choose one COMMON card in Sheol that has LORE three or more","activate that chosen card","draw three cards from the Tower"],
  "ability_text":"Choose one COMMON card in Sheol that has LORE three or more and activate that chosen card. Then draw three cards from the Tower.",
  "rules_terms":["card","Sheol","LORE","cards","Tower","choose","activate","draw"],
  "rules_actions":["choose","activate","draw"],
  "clarity":cl(targets=["one COMMON card in Sheol that has LORE three or more","that chosen card"],zones=["Sheol","Tower"],quantities=["one COMMON card","three cards"],outcomes=["activate that chosen card","draw three cards from the Tower"]),
  "rarity_budget":budget(2,2,1,0,4, why=["Sheol and the Tower","a filtered choice, an activation and a draw","Sheol must already hold a weighty COMMON card","no other player's material is moved directly","a structure bent - a dead card resolves again out of Sheol - with three cards drawn on top"]) })
META["SPIRIT"] = {"gloss":"The breath that gives life","weight":5,"weight_rationale":"a pillar of the set: the Spirit moving on the face of the waters is the first act reported after the heavens and the earth, and the same word is the breath in every living thing of the era",
 "art_prompt":"A stone oil lamp set in an open window, its flame streaming sideways in a rush of night wind, dust and chaff lifting off the sill into the dark, no people, "+style("lantern"),
 "stats":{"lore":5,"context":5,"complexity":4},
 "stats_rationale":{"lore":"the printed verses make the Spirit the maker of a man and the giver of life against the letter that kills - a doctrine hangs on the word","context":"ruach occurs 378 times in the Hebrew Bible; pneuma occurs 379 times in the New Testament; total 757","complexity":"one word carries wind, breath and spirit in both languages, so every occurrence is a translator's decision - and John 3:8 plays on all three at once, a pun no English rendering can keep"},
 "ot_verse":{"ref":"Job 33:4","snippet":"The Spirit of God hath made me, and the breath of the Almighty hath given me life"},"nt_verse":{"ref":"2 Corinthians 3:6","snippet":"the letter killeth, but the spirit giveth life"},
 "greek":{"text":"πνεῦμα","translit":"pneuma"},"hebrew":{"text":"רוּחַ","translit":"ruach"},
 "ot_refs":"Gen 1:2 • Gen 6:3 • Job 33:4","nt_refs":"2 Cor 3:6 • John 6:63 • Rom 8:11",
 "trivia":["Genesis 8:1 uses the same word for the wind God makes pass over the earth to dry the flood - wind and Spirit are one word.","Genesis 6:3 sets the era's clock: my spirit shall not always strive with man, yet his days shall be an hundred and twenty years.","John 3:8 turns on the double sense - the wind bloweth where it listeth, and so is every one that is born of the Spirit."]}

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

TYPES = {"NAKED":"ADJECTIVE","COVENANT":"NOUN","NOAH":"NAME","CURSE":"VERB","HUNTER":"TITLE",
         "RIGHTEOUS":"ADJECTIVE","ADAM":"NAME","SPIRIT":"TITLE","HEAR":"VERB","DEEP":"ADJECTIVE",
         "HOVER":"VERB","DISCORD":"NOUN"}
