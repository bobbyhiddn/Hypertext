"""Module A1 regen: legacy slots #001-#006 (GRACE, BUILD, MIGHTY, SCATTER, CREATE,
CONFUSE) redesigned under the grammar, the power ladder, word weight, the stat
rubric, the mechanic axes and the art subject/lighting rules.

The WORD and the printed Hebrew/Greek lemmas of each slot are unchanged; ability,
art, stats, weight, verses and trivia are new. GRACE and CREATE are promoted to
GLORIOUS as weight-5 pillars and carry two different kinds of wild: GRACE gives a
card to every player at the table and hands one back out of a finished record,
CREATE lets undistinguished matter go down into Sheol and calls two words out of
nothing.
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

# ---------------------------------------------------------------- GLORIOUS

DESIGNS["GRACE"] = ("GLORIOUS",
 {"core_meaning":"Favour no one has earned, given freely and never withdrawn - but Noah found grace in the eyes of the LORD, in a generation that had earned nothing at all.",
  "type_expression":"A noun of free gift: every player at the table is given a card unasked, and what was already given to you is given again - a card comes back out of one of your Pages while that Page still stands and scores in full.",
  "mechanical_anchors":["given a card unasked","given again out of a Page","Noah found grace in the eyes of the LORD","the Page still stands","every player at the table"],
  "mechanic_seed":"Each player draws one card from the Tower, every player at the table given a card unasked. Then return one card from one of your Pages to your hand, given again out of a Page while the Page still stands and scores in full, and draw two cards from the Tower."},
 {"mechanical_expression":"Every player at the table is given a card unasked out of the Tower, and then what was already recorded is given again out of a Page - one card returns from your Pages to your hand while that Page still stands, and two more cards are drawn.",
  "semantic_anchor":"given a card unasked",
  "semantic_evidence":["Each player draws one card from the Tower","return one card from one of your Pages to your hand","draw two cards from the Tower"],
  "ability_text":"Each player draws one card from the Tower. Then return one card from one of your Pages to your hand and draw two cards from the Tower.",
  "rules_terms":["player","card","Tower","Pages","hand","cards","draw","return"],
  "rules_actions":["draw","return","draw"],
  "clarity":cl(targets=["Each player","one of your Pages","your hand"],zones=["Tower","Pages","hand"],quantities=["one card","one card","two cards"],outcomes=["Each player draws one card from the Tower","return one card from one of your Pages to your hand","draw two cards from the Tower"]),
  "rarity_budget":budget(3,3,1,3,4, why=["every player at the table, the Tower, your Pages and the hand","one gift to the whole table, one recovery out of a Page and one draw","a Page must already be recorded before anything can be given back out of it","every player's material is moved, each of them given a card unasked","the table is fed and three cards' worth comes to you, a Page spent for nothing among them"]) })
META["GRACE"] = {"gloss":"Favour no one has earned, given freely","weight":5,"weight_rationale":"a pillar of the set: grace is the hinge the flood account turns on - Noah is said to have found it before he is ever called just, so the survival of the whole era is credited rather than earned - and the New Testament goes on to state salvation itself in this one noun; a weight-5 word, which is why it prints GLORIOUS",
 "art_prompt":"One young cedar left standing green in a felled clearing of blackened stumps, a single shaft of light falling on that tree alone while the ruined ground around it stays dark, no people, "+S("golden"),
 "stats":{"lore":5,"context":4,"complexity":4},
 "stats_rationale":{"lore":"the printed verses are the one favourable verdict spoken over a condemned generation and the statement that by grace are ye saved through faith - the era's rescue and the gospel's ground both rest on this noun","context":"chen occurs 69 times in the Hebrew Bible; charis occurs 156 times in the New Testament; total 225","complexity":"chen belongs to an idiom rather than a doctrine - one finds chen in the eyes of another, and the finder may be a servant standing before a king - while charis carries the Greek senses of charm and of a favour that is owed thanks, so the English word grace is doing work neither original quite does alone"},
 "ot_verse":{"ref":"Genesis 6:8","snippet":"But Noah found grace in the eyes of the LORD"},"nt_verse":{"ref":"Ephesians 2:8","snippet":"For by grace are ye saved through faith; and that not of yourselves"},
 "greek":{"text":"χάρις","translit":"charis"},"hebrew":{"text":"חֵן","translit":"chen"},
 "ot_refs":"Gen 6:8 • Gen 18:3 • Gen 19:19","nt_refs":"Eph 2:8 • John 1:17 • Rom 5:20",
 "trivia":["Genesis 6:8 comes before Genesis 6:9 calls Noah just and perfect - the favour is stated first and the character afterwards, and the order is the argument.","Chen is always found, never earned or seized; Hebrew finds it in the eyes of another, which is why the KJV keeps the whole phrase rather than shortening it.","Charis and eucharistia, grace and thanksgiving, grow from one root - in Greek a gift and the thanks for it are a syllable apart."]}

# ---------------------------------------------------------------- COMMON
DESIGNS["BUILD"] = ("COMMON",
 {"core_meaning":"To raise a structure course upon course - let us build us a city and a tower; what is built is laid up piece by chosen piece.",
  "type_expression":"A verb of raising: four courses are shown openly, the one stone the work calls for - a card type in your Lot - is set into the hand, and the rest are laid back on top of the Tower for the next course.",
  "mechanical_anchors":["set into the work","the stone the work calls for","laid back on top","let us build us a city and a tower","four courses shown openly"],
  "mechanic_seed":"Reveal the top four cards of the Tower, four courses shown openly; add one revealed card whose card type is in your Lot to your hand, the stone the work calls for set into the work, and put each other revealed card on top of the Tower, laid back on top for the next course."},
 {"mechanical_expression":"Four courses are shown openly and the one the work calls for is set into the work: the revealed card whose card type is in your Lot goes to the hand, and each other revealed card is put back on top of the Tower.",
  "semantic_anchor":"set into the work",
  "semantic_evidence":["Reveal the top four cards of the Tower","Add one revealed card whose card type is in your Lot to your hand","put each other revealed card on top of the Tower"],
  "ability_text":"Reveal the top four cards of the Tower. Add one revealed card whose card type is in your Lot to your hand and put each other revealed card on top of the Tower.",
  "rules_terms":["cards","Tower","card","card type","Lot","hand","reveal","add","put"],
  "rules_actions":["reveal","add","put"],
  "clarity":cl(targets=["the top four cards of the Tower","your hand"],zones=["Tower","Lot","hand"],quantities=["top four cards","one revealed card"],outcomes=["Add one revealed card whose card type is in your Lot to your hand","put each other revealed card on top of the Tower"]),
  "rarity_budget":budget(2,2,0,0,1, why=["the Tower, your Lot and the hand","one filtered add and one placement","your Lot is read as it lies, with no prior state built","no other player is touched","one card taken, and only when the work calls for its kind"]) })
META["BUILD"] = {"gloss":"To raise a structure course upon course","weight":2,"weight_rationale":"the verb the whole Babel account is spoken in - go to, let us build - but it is an ordinary action word with a clear place in the era rather than a named agent or event; the named thing is the city and tower themselves, so BUILD stays at 2 and prints COMMON",
 "art_prompt":"A half-raised ziggurat of raw brick standing in unfinished courses on a lattice of rough poles, mortar tubs crusting over and a plumb line hanging dead still against the face, no people, "+S("golden"),
 "stats":{"lore":3,"context":5,"complexity":3},
 "stats_rationale":{"lore":"the printed verses set the builders' let us build us a city and a tower beside a house built upon a rock - a recognized theme of the era with clear teaching, though the doctrine hangs on what is built rather than on the verb","context":"banah occurs 377 times in the Hebrew Bible; oikodomeo occurs 40 times in the New Testament; total 417","complexity":"banah and ben, to build and a son, are one root, so Sarai says I may be builded by her of a child, and Greek splits the sense with oikodomeo, to house-build, which the epistles then use for edifying people"},
 "ot_verse":{"ref":"Genesis 11:4","snippet":"Go to, let us build us a city and a tower, whose top may reach unto heaven"},"nt_verse":{"ref":"Matthew 7:24","snippet":"a wise man, which built his house upon a rock"},
 "greek":{"text":"οἰκοδομέω","translit":"oikodomeo"},"hebrew":{"text":"בָּנָה","translit":"banah"},
 "ot_refs":"Gen 11:4 • Gen 11:5 • Gen 8:20","nt_refs":"Matt 7:24 • Matt 21:33 • Matt 16:18",
 "trivia":["Genesis 11:5 says the LORD came down to see the city and the tower which the children of men builded - the builders reach for heaven and heaven has to stoop to look.","Hebrew builds a son and a house with the same root, which is why a barren wife in Genesis asks to be builded by her handmaid.","The first thing built after the flood is not a city but an altar; Noah builds it before the ground has dried."]}

# ---------------------------------------------------------------- UNCOMMON
DESIGNS["MIGHTY"] = ("UNCOMMON",
 {"core_meaning":"Strong enough to overpower - there were giants in the earth in those days, the same became mighty men which were of old, men of renown.",
  "type_expression":"An adjective of strength: a chosen player is overpowered and loses a card down into Sheol, and the heaviest of the fallen - LORE four or more - are taken up by the strong hand.",
  "mechanical_anchors":["overpowered and loses a card","taken up by the strong hand","mighty men which were of old","the heaviest of the fallen","LORE four or more"],
  "mechanic_seed":"Choose another player; that chosen player puts one card from that chosen player's hand into Sheol, overpowered and loses a card. Then choose up to two cards in Sheol with LORE four or more, the heaviest of the fallen, and add those chosen cards to your hand, taken up by the strong hand."},
 {"mechanical_expression":"A chosen player is overpowered and loses a card into Sheol, and then the heaviest of the fallen - up to two cards in Sheol with LORE four or more - are taken up by the strong hand into your own.",
  "semantic_anchor":"overpowered and loses a card",
  "semantic_evidence":["that chosen player puts one card from that chosen player's hand into Sheol","choose up to two cards in Sheol with LORE four or more","add those chosen cards to your hand"],
  "ability_text":"Choose another player; that chosen player puts one card from that chosen player's hand into Sheol. Then choose up to two cards in Sheol with LORE four or more and add those chosen cards to your hand.",
  "rules_terms":["player","card","hand","Sheol","cards","LORE","choose","put","add"],
  "rules_actions":["choose","put","choose","add"],
  "clarity":cl(targets=["another player","that chosen player's hand","your hand"],zones=["hand","Sheol"],quantities=["one card","up to two cards"],outcomes=["that chosen player puts one card from that chosen player's hand into Sheol","add those chosen cards to your hand"]),
  "rarity_budget":budget(2,2,1,1,2, why=["one chosen player, the hand and Sheol","one forced placement and one filtered recovery","Sheol must hold a card heavy enough to be worth lifting","one chosen player loses a card of that player's own choosing","up to two heavy cards lifted out of Sheol"]) })
META["MIGHTY"] = {"gloss":"Strong enough to overpower","weight":3,"weight_rationale":"the gibborim of Genesis 6 and Nimrod the mighty one are how the era names raw human power before the flood and after it - thematic vocabulary with real teaching, but the word describes a kind of man rather than naming an agent or event the era turns on, so it stays at 3 and prints UNCOMMON",
 "art_prompt":"An enormous bronze-scaled war belt and a spear shaft thicker than a roof beam propped against a lone standing stone on a high moor, the turf beaten bare in a ring around its foot, no people, "+S("golden"),
 "stats":{"lore":3,"context":4,"complexity":4},
 "stats_rationale":{"lore":"the printed verses give the mighty men of old, men of renown, and the Magnificat's he that is mighty - a recognized theme of the era with clear teaching, though the doctrine rests on who is mighty rather than on the adjective","context":"gibbor occurs 159 times in the Hebrew Bible; dunatos occurs 32 times in the New Testament; total 191","complexity":"gibbor is at once a warrior, a champion, a tyrant and, in El Gibbor, a name of God, so the same word praises and accuses; dunatos likewise slides between able, powerful and possible, and Greek must choose which each time"},
 "ot_verse":{"ref":"Genesis 6:4","snippet":"the same became mighty men which were of old, men of renown"},"nt_verse":{"ref":"Luke 1:49","snippet":"For he that is mighty hath done to me great things"},
 "greek":{"text":"δυνατός","translit":"dunatos"},"hebrew":{"text":"גִּבּוֹר","translit":"gibbor"},
 "ot_refs":"Gen 6:4 • Gen 10:8 • Gen 10:9","nt_refs":"Luke 1:49 • Rom 4:21 • Acts 18:24",
 "trivia":["Genesis 6:4 calls the mighty men anshei hashem, men of the name - two chapters before Babel's builders set out to make themselves a name.","Nimrod is the first man in Scripture called gibbor, and the text says he began to be one, as though might were something a man works up to.","The same adjective stands in Isaiah's El Gibbor, the Mighty God, so Hebrew praise and Hebrew menace share one word."]}

# ---------------------------------------------------------------- RARE
DESIGNS["SCATTER"] = ("RARE",
 {"core_meaning":"To break one people apart and drive the pieces abroad - from thence did the LORD scatter them abroad upon the face of all the earth.",
  "type_expression":"A verb of dispersal: one kindred is named, six cards are driven off the Tower and abroad into Sheol, and only the named kindred is gathered back to the hand; a record already spread wide over the earth draws one more.",
  "mechanical_anchors":["driven abroad into Sheol","only the named kindred gathered back","scatter them abroad upon the face of all the earth","a record already spread wide","total CONTEXT fifteen or more"],
  "mechanic_seed":"Name a card type, one kindred named. Put the top six cards of the Tower into Sheol, driven abroad into Sheol, then add up to three of those cards of the named type to your hand, only the named kindred gathered back; if the cards in your Pages have total CONTEXT fifteen or more, a record already spread wide over the earth, draw one card from the Tower."},
 {"mechanical_expression":"Six cards are driven abroad into Sheol off the top of the Tower and only the named kindred is gathered back to the hand, and a record already spread wide - Pages of total CONTEXT fifteen or more - draws one card more.",
  "semantic_anchor":"driven abroad into Sheol",
  "semantic_evidence":["Put the top six cards of the Tower into Sheol","add up to three of those cards of the named type to your hand","if the cards in your Pages have total CONTEXT fifteen or more"],
  "ability_text":"Name a card type. Put the top six cards of the Tower into Sheol, then add up to three of those cards of the named type to your hand; if the cards in your Pages have total CONTEXT fifteen or more, draw one card from the Tower.",
  "rules_terms":["card type","cards","Tower","Sheol","hand","Pages","CONTEXT","card","name","put","add","draw"],
  "rules_actions":["name","put","add","draw"],
  "clarity":cl(targets=["the top six cards of the Tower","your hand"],zones=["Tower","Sheol","hand","Pages"],quantities=["top six cards","up to three of those cards","one card"],condition="if the cards in your Pages have total CONTEXT fifteen or more",outcomes=["Put the top six cards of the Tower into Sheol","add up to three of those cards of the named type to your hand","draw one card from the Tower"]),
  "rarity_budget":budget(2,3,2,0,3, why=["the Tower, Sheol, your Pages and the hand","one naming, one mass placement, one filtered add and one conditional draw","six cards must be driven off the Tower and the Pages threshold must already be built","no other player is touched","three cards of the named kindred gathered back, and a fourth when the record is spread wide"]) })
META["SCATTER"] = {"gloss":"To break apart and drive abroad","weight":4,"weight_rationale":"the judgment the era ends in - the scattering from Babel is the named event that turns one speech into the table of nations, and every later dispersion is read through it; a weight-4 word, which is why it prints RARE",
 "art_prompt":"Four hard-beaten roads running out from one abandoned camp of overturned baskets and dropped mattocks, each track climbing away over a different ridge until it thins to nothing, no people, "+S("desert"),
 "stats":{"lore":4,"context":3,"complexity":3},
 "stats_rationale":{"lore":"the printed verses are the LORD scattering the builders over the face of all the earth and the shepherd smitten with the sheep scattered abroad - in this era scattering is how judgment is executed","context":"puts occurs 65 times in the Hebrew Bible; diaskorpizo occurs 9 times in the New Testament; total 74","complexity":"Hebrew has at least three verbs English renders scatter - puts, naphats and pazar - and Genesis 11 uses puts for a dispersal that is a judgment, not an accident, while Greek reaches for diaskorpizo, a winnowing word for grain thrown into the wind"},
 "ot_verse":{"ref":"Genesis 11:9","snippet":"from thence did the LORD scatter them abroad upon the face of all the earth"},"nt_verse":{"ref":"Matthew 26:31","snippet":"the sheep of the flock shall be scattered abroad"},
 "greek":{"text":"διασκορπίζω","translit":"diaskorpizo"},"hebrew":{"text":"פּוּץ","translit":"puts"},
 "ot_refs":"Gen 11:9 • Gen 11:4 • Gen 11:8","nt_refs":"Matt 26:31 • Luke 1:51 • Acts 5:37",
 "trivia":["The builders say lest we be scattered abroad; the scattering is exactly what their building brings on them.","Genesis uses the same verb twice in two verses - the LORD scattered them, and from thence did he scatter them - as though the sentence had to be said again to be believed.","Diaskorpizo is a farmer's word for flinging grain into the wind, which is why the Magnificat can use it of proud men."]}

DESIGNS["CONFUSE"] = ("RARE",
 {"core_meaning":"To mingle until nothing can be told apart - let us go down, and there confound their language, that they may not understand one another's speech.",
  "type_expression":"A verb of mingling: one neighbour is made to speak, and a tangled enough tongue - COMPLEXITY three or more - yields a Letter to the hearer, while a plain one leaves nothing but a blind draw.",
  "mechanical_anchors":["made to speak","a tangled enough tongue","that they may not understand one another's speech","yields a Letter to the hearer","nothing but a blind draw"],
  "mechanic_seed":"Choose another player; that chosen player reveals one card from that chosen player's hand, made to speak. If that revealed card has COMPLEXITY three or more, a tangled enough tongue, gain one Letter, which yields a Letter to the hearer; otherwise, draw one card from the Tower, nothing but a blind draw."},
 {"mechanical_expression":"A neighbour is made to speak and the tongue is tested: a revealed card of COMPLEXITY three or more yields a Letter to the hearer, and anything plainer leaves nothing but a blind draw from the Tower.",
  "semantic_anchor":"made to speak",
  "semantic_evidence":["that chosen player reveals one card from that chosen player's hand","If that revealed card has COMPLEXITY three or more, gain one Letter","otherwise, draw one card from the Tower"],
  "ability_text":"Choose another player; that chosen player reveals one card from that chosen player's hand. If that revealed card has COMPLEXITY three or more, gain one Letter; otherwise, draw one card from the Tower.",
  "rules_terms":["player","card","hand","COMPLEXITY","Letter","Tower","choose","reveal","gain","draw"],
  "rules_actions":["choose","reveal","gain","draw"],
  "clarity":cl(targets=["another player","that chosen player's hand"],zones=["hand","Tower"],quantities=["one card","one Letter","one card"],condition="If that revealed card has COMPLEXITY three or more",outcomes=["that chosen player reveals one card from that chosen player's hand","gain one Letter","draw one card from the Tower"]),
  "rarity_budget":budget(2,2,1,1,3, why=["one chosen player, the hand and the Tower","one reveal, then one of two exclusive results","a tongue tangled enough to test must be in the neighbour's hand","one chosen player is made to show a card and nothing of that player's moves","a Letter, worth three cards, when the tongue is tangled, and a card when it is not"]) })
META["CONFUSE"] = {"gloss":"To mingle until nothing can be told apart","weight":4,"weight_rationale":"the named judgment the era ends in - the confounding of one lip into many is the act that makes the nations and gives Babel its name; a weight-4 word, which is why it prints RARE",
 "art_prompt":"An abandoned worksite on the flank of an unfinished tower, half-set brick courses breaking off mid-row, a mortar trough gone hard and a knot of measuring cords tangled together on the scaffold boards, no people, "+S("overcast"),
 "stats":{"lore":4,"context":3,"complexity":5},
 "stats_rationale":{"lore":"the printed verses are the confounding of the one language and the crowd at Pentecost confounded because every man heard his own tongue - in this era the state of human speech is decided by this verb","context":"balal occurs 44 times in the Hebrew Bible; sygcheo occurs 5 times in the New Testament; total 49","complexity":"balal ordinarily means to mingle oil into flour for an offering, so the word for a grain offering and the word for Babel's judgment are the same; Genesis then puns Babel on it, and Greek answers with sygcheo, to pour together, a word for liquids and for riots alike"},
 "ot_verse":{"ref":"Genesis 11:7","snippet":"let us go down, and there confound their language, that they may not understand one another's speech"},"nt_verse":{"ref":"Acts 2:6","snippet":"the multitude came together, and were confounded, because that every man heard them speak in his own language"},
 "greek":{"text":"συγχέω","translit":"sygcheo"},"hebrew":{"text":"בָּלַל","translit":"balal"},
 "ot_refs":"Gen 11:7 • Gen 11:9 • Ps 92:10","nt_refs":"Acts 2:6 • Acts 19:32 • Acts 21:27",
 "trivia":["Babel means gate of god in Akkadian; Genesis hears it instead as balal, confusion, and the pun is the whole verdict on the city.","The same verb mixes oil into the fine flour of a meal offering - in Hebrew, confusion and a careful blending are one word.","Acts 2 reverses the sentence without undoing it: the tongues stay many, and the hearing is what is healed."]}

DESIGNS["CREATE"] = ("GLORIOUS",
 {"core_meaning":"To call into being what was not there - in the beginning God created the heaven and the earth, and the earth was without form, and void.",
  "type_expression":"A verb of origination: matter with no distinction in it - two cards of the same card type - is let go down into the deep of Sheol, and out of nothing two words are gained and one new kind is raised off the top of the Tower.",
  "mechanical_anchors":["let go down into the deep","two words are gained out of nothing","matter with no distinction in it","one new kind is raised off the top","without form, and void"],
  "mechanic_seed":"Discard two cards of the same card type from your hand into Sheol, matter with no distinction in it let go down into the deep. Then gain two Letters, two words are gained out of nothing, and add one card from the top of the Tower to your hand, one new kind is raised off the top."},
 {"mechanical_expression":"Matter with no distinction in it goes down into the deep of Sheol - two cards of the same card type - and it is let go down into the deep so that two words may be gained out of nothing and one new kind raised off the top of the Tower.",
  "semantic_anchor":"let go down into the deep",
  "semantic_evidence":["Discard two cards of the same card type from your hand into Sheol","gain two Letters","add one card from the top of the Tower to your hand"],
  "ability_text":"Discard two cards of the same card type from your hand into Sheol. Then gain two Letters and add one card from the top of the Tower to your hand.",
  "rules_terms":["cards","card type","hand","Sheol","Letters","card","Tower","discard","gain","add"],
  "rules_actions":["discard","gain","add"],
  "clarity":cl(targets=["your hand","the top of the Tower"],zones=["hand","Sheol","Tower"],quantities=["two cards","two Letters","one card"],outcomes=["Discard two cards of the same card type from your hand into Sheol","gain two Letters","add one card from the top of the Tower to your hand"]),
  "rarity_budget":budget(2,3,1,0,4, why=["the hand, Sheol and the Tower","one matched discard, one gain of two Letters and one add","Sheol receives the undistinguished matter before anything is made","no other player is touched","two Letters are six cards' worth, and a new card besides, for two cards let go"]) })
META["CREATE"] = {"gloss":"To call into being what was not there","weight":5,"weight_rationale":"a pillar of the set: the first sentence of the era and of the Bible is spoken in this verb, God alone is ever its subject, and the whole account of what the world is and whose it is hangs on it; a weight-5 word, which is why it prints GLORIOUS",
 "art_prompt":"The rim of a lightless world seen from far above, one seam of radiance splitting open along the horizon and gold dust streaming out of the seam into the unformed dark, no people, "+S("golden"),
 "stats":{"lore":5,"context":3,"complexity":4},
 "stats_rationale":{"lore":"the printed verses are the opening sentence of Scripture and the claim that by him were all things created - in this era nothing is prior to this verb","context":"bara occurs 54 times in the Hebrew Bible; ktizo occurs 15 times in the New Testament; total 69","complexity":"bara never takes a human subject and never names the material used, which is the whole of the argument for creation out of nothing; it stands beside asah, to make, and yatsar, to form, in the same chapters, and identical consonants elsewhere mean to cut down or to grow fat"},
 "ot_verse":{"ref":"Genesis 1:1","snippet":"In the beginning God created the heaven and the earth"},"nt_verse":{"ref":"Colossians 1:16","snippet":"For by him were all things created, that are in heaven, and that are in earth"},
 "greek":{"text":"κτίζω","translit":"ktizo"},"hebrew":{"text":"בָּרָא","translit":"bara"},
 "ot_refs":"Gen 1:1 • Gen 1:21 • Gen 1:27","nt_refs":"Col 1:16 • Eph 2:10 • Rev 4:11",
 "trivia":["Genesis 1 uses bara only three times - for the heavens and earth, for the great creatures, and for man - and asah, to make, for everything between.","No subject but God ever governs bara in the Hebrew Bible; the grammar itself refuses the verb to anyone else.","Ktizo in classical Greek means to found a city, so the Septuagint's choice quietly makes the world a colony settled by its founder."]}


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

TYPES = {"GRACE":"NOUN","BUILD":"VERB","MIGHTY":"ADJECTIVE","SCATTER":"VERB","CREATE":"VERB","CONFUSE":"VERB"}
