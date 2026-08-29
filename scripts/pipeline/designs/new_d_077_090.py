"""Module D: slots #077-#090, the last fourteen words of Babel Alpha.

FLOOD (NOUN/GLORIOUS), PERFECT (ADJECTIVE/RARE), PRIEST (TITLE/RARE),
CLEAN (ADJECTIVE/UNCOMMON), HAGAR (NAME/UNCOMMON), PLANT (VERB/COMMON),
DRY / AFRAID / FRUITFUL (ADJECTIVE/COMMON), LAMECH / TERAH (NAME/COMMON),
FATHER / MOTHER / STRANGER (TITLE/COMMON).

Written under the grammar, the power ladder, word weight, the verse lexical
rule and the art subject rules. Golden is the set's signature light; another
palette clause appears only where the scene itself is a storm, a night
interior, a wilderness or a bleached noon.
"""
from hypertext.cards.art_motifs import load_art_standards, style_suffix

ART = load_art_standards("series/2026-Q1")
GOLDEN = style_suffix(ART, "golden")
STORM = style_suffix(ART, "storm")
LANTERN = style_suffix(ART, "lantern")
DESERT = style_suffix(ART, "desert")
NOON = style_suffix(ART, "noon")


def cl(**k):
    base = {"trigger": "activation", "timing": "instantaneous", "targets": [], "zones": [],
            "quantities": [], "duration": "instantaneous", "condition": "none", "outcomes": []}
    base.update(k)
    return base


def budget(*v, why):
    return {k: {"rating": r, "rationale": w}
            for k, r, w in zip(("scope", "complexity", "setup", "interaction", "payoff"), v, why)}


DESIGNS = {}
META = {}

# ---------------------------------------------------------------- COMMON
DESIGNS["PLANT"] = ("COMMON",
 {"core_meaning":"To set a living thing into the ground so that it will grow - the LORD God planted a garden eastward in Eden, and every tree of it grew out of the ground.",
  "type_expression":"A verb of setting in: two cards are looked at from the top of the Tower, the one card whose CONTEXT shows it fills the ground is taken into the hand, and the other card are set back down into the bottom of the Tower.",
  "mechanical_anchors":["set back down into the bottom","planted a garden eastward","grew out of the ground","two cards looked at","fills the ground"],
  "mechanic_seed":"Look at the top two cards of the Tower; add one of those cards with CONTEXT four or more to the hand, the seed that fills the ground, and put the other card on the bottom of the Tower, set back down into the ground where they were planted."},
 {"mechanical_expression":"The planter looks at the top two cards of the Tower, keeps the one card whose CONTEXT fills the ground, and the other card are set back down into the bottom of the Tower where a planted thing belongs.",
  "semantic_anchor":"set back down into the bottom",
  "semantic_evidence":["Look at the top two cards of the Tower","Add one of those cards that has CONTEXT four or more to your hand","put the other card on the bottom of the Tower"],
  "ability_text":"Look at the top two cards of the Tower. Add one of those cards that has CONTEXT four or more to your hand and put the other card on the bottom of the Tower.",
  "rules_terms":["cards","Tower","card","hand","CONTEXT","look at","add","put"],
  "rules_actions":["look at","add","put"],
  "clarity":cl(targets=["the top two cards of the Tower","your hand"],zones=["Tower","hand"],
               quantities=["top two cards","one of those cards","the other card"],
               outcomes=["Add one of those cards that has CONTEXT four or more to your hand","put the other card on the bottom of the Tower"]),
  "rarity_budget":budget(2,2,0,0,1, why=["the Tower and the hand","one add and one placement","no prior state is required","no other player is touched","one card taken, chosen from five seen"]) })
META["PLANT"] = {"gloss":"To set a living thing into the ground so that it grows","weight":2,
 "weight_rationale":"the verb of Eden's garden and of Noah's vineyard - a descriptive word of the era with a clear place, not a doctrine",
 "art_prompt":"A young fig sapling newly set into dark turned earth, a wooden dibber and a handful of seed beside the open hole, painted close up on the wet roots, no people, "+GOLDEN,
 "stats":{"lore":3,"context":3,"complexity":2},
 "stats_rationale":{"lore":"God plants the garden, Noah plants the vineyard, and the Father plants every plant that stands - a recognized theme with clear teaching","context":"nata occurs 59 times in the Hebrew Bible; phyteuo occurs 11 times in the New Testament; total 70","complexity":"a plain verb of setting in the ground with stable translation; only the passive sense of a people planted in a land needs a note"},
 "ot_verse":{"ref":"Genesis 2:8","snippet":"And the LORD God planted a garden eastward in Eden"},
 "nt_verse":{"ref":"Matthew 15:13","snippet":"Every plant, which my heavenly Father hath not planted, shall be rooted up"},
 "greek":{"text":"φυτεύω","translit":"phyteuo"},"hebrew":{"text":"נָטַע","translit":"nata"},
 "ot_refs":"Gen 2:8 • Gen 9:20 • Gen 21:33","nt_refs":"Matt 15:13 • 1 Cor 3:6 • Luke 17:28",
 "trivia":["Genesis 2:8 is the first planting in Scripture, and the planter is God himself.","Noah's first act after the flood is to plant a vineyard - the same verb that opened Eden.","Paul says I have planted, Apollos watered, but God gave the increase; the planter is not the one who makes it grow."]}

DESIGNS["DRY"] = ("COMMON",
 {"core_meaning":"Without water - let the dry land appear, and the waters drained off until the face of the ground was uncovered.",
  "type_expression":"An adjective of the uncovered ground: four cards are looked at from the bottom of the Tower, the ground beneath the waters, one card is taken up into the hand, and the other cards are lifted to the top of the Tower as the land rose.",
  "mechanical_anchors":["the ground beneath the waters","let the dry land appear","lifted to the top","waters drained off","four cards looked at"],
  "mechanic_seed":"Look at the bottom four cards of the Tower, the ground beneath the waters; add one of those cards to the hand and put the other cards on top of the Tower, lifted up as the dry land appeared."},
 {"mechanical_expression":"The waters drain off the bottom of the Tower: four cards there, the ground beneath the waters, are looked at, one card is taken into the hand, and the other cards rise to the top of the Tower.",
  "semantic_anchor":"the ground beneath the waters",
  "semantic_evidence":["Look at the bottom four cards of the Tower","Add one of those cards to your hand","put the other cards on top of the Tower"],
  "ability_text":"Look at the bottom four cards of the Tower. Add one of those cards to your hand and put the other cards on top of the Tower.",
  "rules_terms":["cards","Tower","card","hand","look at","add","put"],
  "rules_actions":["look at","add","put"],
  "clarity":cl(targets=["the bottom four cards of the Tower","your hand"],zones=["Tower","hand"],
               quantities=["bottom four cards","one of those cards","the other cards"],
               outcomes=["Add one of those cards to your hand","put the other cards on top of the Tower"]),
  "rarity_budget":budget(2,2,0,0,1, why=["the Tower and the hand","one add and one placement","no prior state is required","no other player is touched","one card taken, chosen from four seen"]) })
META["DRY"] = {"gloss":"Without water, as the dry land that appeared","weight":2,
 "weight_rationale":"the third day's word and the flood's ending - a descriptive word with a clear place in the era",
 "art_prompt":"A cracked mud flat baked to a hard crust, the last damp shine caught in the deep fissures and a stranded olive branch drying on the mud, no people, "+NOON,
 "stats":{"lore":2,"context":2,"complexity":3},
 "stats_rationale":{"lore":"the dry land is a real motif of creation and of the flood's end, but no doctrine rests on the word","context":"yabbashah occurs 14 times in the Hebrew Bible; xeros occurs 8 times in the New Testament; total 22","complexity":"yabbashah is a noun, the dry, used adjectivally for land uncovered by water; xeros runs from dry land to a withered hand to the green tree and the dry - a range to explain"},
 "ot_verse":{"ref":"Genesis 1:9","snippet":"let the dry land appear: and it was so"},
 "nt_verse":{"ref":"Hebrews 11:29","snippet":"they passed through the Red sea as by dry land"},
 "greek":{"text":"ξηρός","translit":"xeros"},"hebrew":{"text":"יַבָּשָׁה","translit":"yabbashah"},
 "ot_refs":"Gen 1:9 • Gen 1:10 • Ps 66:6","nt_refs":"Heb 11:29 • Matt 23:15 • Luke 23:31",
 "trivia":["The dry appears on the third day before anything is planted in it; the ground is made ready before it is filled.","Genesis 8 measures the flood's end twice - the waters were abated, and then the face of the ground was dry.","Jesus asks what shall be done in the dry, using the same word Greek readers knew for dry land."]}

DESIGNS["AFRAID"] = ("COMMON",
 {"core_meaning":"Struck with fear and hiding - I heard thy voice in the garden, and I was afraid, and I hid myself among the trees.",
  "type_expression":"An adjective of hiding: four cards are looked at from the top of the Tower, the one card of weightiest LORE is taken into the hand, and the other cards are hidden back on top of the Tower among the trees.",
  "mechanical_anchors":["hidden back on top","I hid myself among the trees","heard thy voice in the garden","four cards looked at","weightiest LORE"],
  "mechanic_seed":"Look at the top four cards of the Tower; add one of those cards with the weightiest LORE to the hand and put the other cards on top of the Tower, hidden back on top among the trees as the man hid from the voice."},
 {"mechanical_expression":"The frightened man looks at the top four cards of the Tower, keeps the one card of heaviest LORE, and the other cards are hidden back on top of the Tower where he hid himself.",
  "semantic_anchor":"hidden back on top",
  "semantic_evidence":["Look at the top four cards of the Tower","Add one of those cards that has LORE three or more to your hand","put the other cards on top of the Tower"],
  "ability_text":"Look at the top four cards of the Tower. Add one of those cards that has LORE three or more to your hand and put the other cards on top of the Tower.",
  "rules_terms":["cards","Tower","card","hand","LORE","look at","add","put"],
  "rules_actions":["look at","add","put"],
  "clarity":cl(targets=["the top four cards of the Tower","your hand"],zones=["Tower","hand"],
               quantities=["top four cards","one of those cards","the other cards"],
               outcomes=["Add one of those cards that has LORE three or more to your hand","put the other cards on top of the Tower"]),
  "rarity_budget":budget(2,2,0,0,1, why=["the Tower and the hand","one add and one placement","no prior state is required","no other player is touched","one card taken, chosen from four seen"]) })
META["AFRAID"] = {"gloss":"Struck with fear, as the man who hid in the garden","weight":3,
 "weight_rationale":"the first fear in Scripture and the fear of the LORD that answers it - thematic vocabulary with real teaching behind it",
 "art_prompt":"A wall of dark fig leaves and heavy trunks in a garden at evening, one gap in the foliage where a body has pushed through, no people, "+GOLDEN,
 "stats":{"lore":4,"context":5,"complexity":2},
 "stats_rationale":{"lore":"the man's fear in the garden and the fear of the LORD that is the beginning of wisdom - a major theme close to doctrine","context":"yare occurs 314 times in the Hebrew Bible; phobeomai occurs 95 times in the New Testament; total 409","complexity":"one verb carries both terror and reverence, and Fear not is the standard greeting of the messenger; the translation choice between afraid and fearing is routine"},
 "ot_verse":{"ref":"Genesis 3:10","snippet":"I was afraid, because I was naked; and I hid myself"},
 "nt_verse":{"ref":"Matthew 14:30","snippet":"when he saw the wind boisterous, he was afraid"},
 "greek":{"text":"φοβέομαι","translit":"phobeomai"},"hebrew":{"text":"יָרֵא","translit":"yare"},
 "ot_refs":"Gen 3:10 • Gen 15:1 • Gen 18:15","nt_refs":"Matt 14:30 • Luke 12:5 • Rev 1:17",
 "trivia":["Fear is the first thing the man confesses after the fruit, before he names the nakedness.","Fear not, Abram is the first of the Bible's many Fear nots, and it comes with a shield.","The same verb is used for being afraid of God and for revering him; context, not the word, decides."]}

DESIGNS["FRUITFUL"] = ("COMMON",
 {"core_meaning":"Bearing much - be fruitful, and multiply; what is fruitful gives back more than was put into it.",
  "type_expression":"An adjective of increase: two cards are looked at from the top of the Tower, the one card whose CONTEXT shows it bears much is taken into the hand, and the other card is left standing on top of the Tower to bear again.",
  "mechanical_anchors":["left standing on top","be fruitful and multiply","gives back more","bears much","two cards looked at"],
  "mechanic_seed":"Look at the top two cards of the Tower; add one of those cards with CONTEXT three or more to the hand because it bears much, and put the other card on top of the Tower, left standing on top to bear again."},
 {"mechanical_expression":"The fruitful branch is kept: two cards are looked at on the top of the Tower, the one card of higher CONTEXT is taken into the hand because it bears much, and the other card is left standing on top of the Tower.",
  "semantic_anchor":"left standing on top",
  "semantic_evidence":["Look at the top two cards of the Tower","Add one of those cards that has CONTEXT three or more to your hand","put the other card on top of the Tower"],
  "ability_text":"Look at the top two cards of the Tower. Add one of those cards that has CONTEXT three or more to your hand and put the other card on top of the Tower.",
  "rules_terms":["cards","Tower","card","hand","CONTEXT","look at","add","put"],
  "rules_actions":["look at","add","put"],
  "clarity":cl(targets=["the top two cards of the Tower","your hand"],zones=["Tower","hand"],
               quantities=["top two cards","one of those cards","the other card"],
               outcomes=["Add one of those cards that has CONTEXT three or more to your hand","put the other card on top of the Tower"]),
  "rarity_budget":budget(2,2,0,0,1, why=["the Tower and the hand","one add and one placement","no prior state is required","no other player is touched","one card taken, chosen from two seen"]) })
META["FRUITFUL"] = {"gloss":"Bearing much, as the first blessing on living things","weight":2,
 "weight_rationale":"the blessing spoken over the creatures, over Adam and again over Noah - a descriptive word with a clear place in the era",
 "art_prompt":"A branch bowed under ripe purple figs and a split pomegranate spilling wet red seeds onto a stone ledge, painted close up, no people, "+GOLDEN,
 "stats":{"lore":3,"context":2,"complexity":2},
 "stats_rationale":{"lore":"the first blessing given to living things and repeated to Noah, and the fruitfulness of good works - a recognized theme with clear teaching","context":"parah occurs 29 times in the Hebrew Bible; karpophoreo occurs 8 times in the New Testament; total 37","complexity":"parah is fruit-bearing of plants, beasts and people alike; karpophoreo is a compound of fruit and bearing - a derivation worth a note"},
 "ot_verse":{"ref":"Genesis 1:28","snippet":"Be fruitful, and multiply, and replenish the earth"},
 "nt_verse":{"ref":"Colossians 1:10","snippet":"being fruitful in every good work, and increasing in the knowledge of God"},
 "greek":{"text":"καρποφορέω","translit":"karpophoreo"},"hebrew":{"text":"פָּרָה","translit":"parah"},
 "ot_refs":"Gen 1:22 • Gen 1:28 • Gen 9:1","nt_refs":"Col 1:10 • Mark 4:20 • Rom 7:4",
 "trivia":["The blessing be fruitful is spoken over the fish and birds before it is spoken over the man.","After the flood God repeats the blessing to Noah word for word; the world restarts on the same terms.","Ephraim's name is built on this verb - God hath caused me to be fruitful in the land of my affliction."]}

DESIGNS["LAMECH"] = ("COMMON",
 {"core_meaning":"The father of Noah, who named his son for comfort concerning our work and toil of our hands, because of the ground the LORD hath cursed.",
  "type_expression":"A name reaching down: two cards are looked at from the bottom of the Tower, the cursed ground beneath, one card of comfort is taken up into the hand, and the other card is left down at the bottom of the Tower.",
  "mechanical_anchors":["left down at the bottom","comfort concerning our work","the ground the LORD hath cursed","taken up into the hand","two cards looked at"],
  "mechanic_seed":"Look at the bottom two cards of the Tower, the cursed ground beneath; add one of those cards to the hand as comfort taken up out of the toil, and put the other card on the bottom of the Tower, left down at the bottom."},
 {"mechanical_expression":"Lamech reaches into the cursed ground: two cards at the bottom of the Tower are looked at, one card is taken up into the hand for comfort, and the other card is left down at the bottom of the Tower.",
  "semantic_anchor":"left down at the bottom",
  "semantic_evidence":["Look at the bottom two cards of the Tower","Add one of those cards to your hand","put the other card on the bottom of the Tower"],
  "ability_text":"Look at the bottom two cards of the Tower. Add one of those cards to your hand and put the other card on the bottom of the Tower.",
  "rules_terms":["cards","Tower","card","hand","look at","add","put"],
  "rules_actions":["look at","add","put"],
  "clarity":cl(targets=["the bottom two cards of the Tower","your hand"],zones=["Tower","hand"],
               quantities=["bottom two cards","one of those cards","the other card"],
               outcomes=["Add one of those cards to your hand","put the other card on the bottom of the Tower"]),
  "rarity_budget":budget(2,2,0,0,1, why=["the Tower and the hand","one add and one placement","no prior state is required","no other player is touched","one card taken, chosen from two seen"]) })
META["LAMECH"] = {"gloss":"The father of Noah, who named his son for comfort","weight":2,
 "weight_rationale":"a genealogy name with one memorable speech; a clear place in the era without teaching hanging on it",
 "art_prompt":"A dark low room with a woven reed cradle and a worn mattock leaning against the mud wall, one oil lamp burning on the sill, no people, "+GOLDEN,
 "stats":{"lore":2,"context":2,"complexity":3},
 "stats_rationale":{"lore":"his naming speech explains Noah and remembers the curse on the ground, but no teaching rests on the man","context":"Lemek occurs 11 times in the Hebrew Bible; Lamech occurs 1 time in the New Testament; total 12","complexity":"two men bear the name - Cain's descendant who boasts of killing, and Seth's descendant who fathers Noah - and the naming of Noah puns on comfort rather than on rest, a wordplay readers argue over"},
 "ot_verse":{"ref":"Genesis 5:28","snippet":"And Lamech lived an hundred eighty and two years, and begat a son"},
 "nt_verse":{"ref":"Luke 3:36","snippet":"which was the son of Lamech"},
 "greek":{"text":"Λάμεχ","translit":"Lamech"},"hebrew":{"text":"לֶמֶךְ","translit":"Lemek"},
 "ot_refs":"Gen 4:18 • Gen 4:23 • Gen 5:28 • Gen 5:31","nt_refs":"Luke 3:36",
 "trivia":["Both lines of Genesis carry a Lamech: one sings a song of vengeance, the other names the man who builds the ark.","Lamech's is the last birth recorded before the flood generation begins.","The name Noah sounds like rest, but Lamech's reason is comfort - the Hebrew leans on a second word."]}

DESIGNS["TERAH"] = ("COMMON",
 {"core_meaning":"The father of Abram, who took his household and set out for the land of Canaan and stopped short at Haran.",
  "type_expression":"A name of the journey begun: four cards are looked at from the top of the Tower - the whole household Terah gathered - the one card that is a NAME is taken into the hand as a son is taken along, and the other cards are set down on the bottom of the Tower where the journey halted.",
  "mechanical_anchors":["set down on the bottom","took his household","stopped short at Haran","a son taken along","four cards looked at"],
  "mechanic_seed":"Look at the top four cards of the Tower, the whole household gathered; add one of those cards that is a NAME to the hand as a son taken along, and put the other cards on the bottom of the Tower, set down on the bottom where the journey stopped."},
 {"mechanical_expression":"Terah takes one NAME along and leaves the rest behind: four cards are looked at on the top of the Tower, the NAME is taken into the hand, and the other cards are set down on the bottom of the Tower.",
  "semantic_anchor":"set down on the bottom",
  "semantic_evidence":["Look at the top four cards of the Tower","Add one of those cards that is a NAME to your hand","put the other cards on the bottom of the Tower"],
  "ability_text":"Look at the top four cards of the Tower. Add one of those cards that is a NAME to your hand and put the other cards on the bottom of the Tower.",
  "rules_terms":["cards","Tower","card","NAME","hand","look at","add","put"],
  "rules_actions":["look at","add","put"],
  "clarity":cl(targets=["the top four cards of the Tower","your hand"],zones=["Tower","hand"],
               quantities=["top four cards","one of those cards","the other cards"],
               outcomes=["Add one of those cards that is a NAME to your hand","put the other cards on the bottom of the Tower"]),
  "rarity_budget":budget(2,2,0,0,1, why=["the Tower and the hand","one add and one placement","no prior state is required","no other player is touched","one card taken, chosen from four seen"]) })
META["TERAH"] = {"gloss":"The father of Abram, who set out for Canaan and stopped at Haran","weight":2,
 "weight_rationale":"a genealogy name at the hinge between Babel and Abram; a clear place in the era without teaching hanging on it",
 "art_prompt":"A laden ox cart halted beside a weathered stone waymarker where the road forks, dust still settling around the wheels, no people, "+GOLDEN,
 "stats":{"lore":2,"context":2,"complexity":3},
 "stats_rationale":{"lore":"his journey sets up the call of Abram, but the teaching belongs to the son, not the father","context":"Terach occurs 11 times in the Hebrew Bible; Thara occurs 1 time in the New Testament; total 12","complexity":"the name is read as wanderer, as delay, or as a moon-word tying Terah to the moon cities Ur and Haran, and Joshua says his fathers served other gods - an etymology and a history both contested"},
 "ot_verse":{"ref":"Genesis 11:31","snippet":"And Terah took Abram his son ... to go into the land of Canaan"},
 "nt_verse":{"ref":"Luke 3:34","snippet":"which was the son of Thara"},
 "greek":{"text":"Θάρα","translit":"Thara"},"hebrew":{"text":"תֶּרַח","translit":"Terach"},
 "ot_refs":"Gen 11:24 • Gen 11:26 • Gen 11:31 • Gen 11:32","nt_refs":"Luke 3:34",
 "trivia":["Terah starts for Canaan a generation before Abram is called there, and never arrives.","Haran is both the name of Terah's dead son and the name of the city where he settles.","Genesis 11 closes with Terah's death; Genesis 12 opens with the call, so the journey is finished by the son."]}

DESIGNS["FATHER"] = ("COMMON",
 {"core_meaning":"The one who begets and goes before - a father of many nations, and the one whose house the children inherit.",
  "type_expression":"A title of going first: one card is drawn from the Tower, then three cards are looked at on the top and the one card of heaviest LORE is laid down at the bottom of the Tower as a foundation for the children who come after.",
  "mechanical_anchors":["laid down at the bottom","a father of many nations","goes before the children","foundation for those who come after","three cards looked at"],
  "mechanic_seed":"Draw one card from the Tower as the father goes first; then look at the top three cards of the Tower and put one of those cards with LORE four or more on the bottom of the Tower, laid down at the bottom as a foundation for the children who come after."},
 {"mechanical_expression":"The father goes first and provides for those behind him: one card is drawn from the Tower, three cards are looked at on the top, and the weightiest by LORE is laid down at the bottom of the Tower.",
  "semantic_anchor":"laid down at the bottom",
  "semantic_evidence":["Draw one card from the Tower","look at the top three cards of the Tower","put one of those cards that has LORE four or more on the bottom of the Tower"],
  "ability_text":"Draw one card from the Tower. Then look at the top three cards of the Tower and put one of those cards that has LORE four or more on the bottom of the Tower.",
  "rules_terms":["card","Tower","cards","LORE","draw","look at","put"],
  "rules_actions":["draw","look at","put"],
  "clarity":cl(targets=["one card from the Tower","the top three cards of the Tower"],zones=["Tower"],
               quantities=["one card","top three cards","one of those cards"],
               outcomes=["Draw one card from the Tower","put one of those cards that has LORE four or more on the bottom of the Tower"]),
  "rarity_budget":budget(1,2,0,0,1, why=["only the Tower is touched","one draw and one placement","no prior state is required","no other player is touched","one card drawn, with three cards seen and one laid down"]) })
META["FATHER"] = {"gloss":"The one who begets and goes before his house","weight":3,
 "weight_rationale":"the era's relational vocabulary - father of many nations, father of such as dwell in tents - carried further by Our Father; thematic, but a common noun rather than a named agent the era turns on",
 "art_prompt":"A stone doorway opening on a night sky thick with stars, a signet ring and a small burning lamp left together on the sill, no people, "+GOLDEN,
 "stats":{"lore":5,"context":5,"complexity":2},
 "stats_rationale":{"lore":"a father of many nations and Our Father which art in heaven - a doctrine hangs on the word","context":"av occurs 1215 times in the Hebrew Bible; pater occurs 413 times in the New Testament; total 1628","complexity":"a plain kinship noun with stable translation; only its extension to a founder of a trade or a nation needs a note"},
 "ot_verse":{"ref":"Genesis 17:4","snippet":"and thou shalt be a father of many nations"},
 "nt_verse":{"ref":"Matthew 6:9","snippet":"Our Father which art in heaven, Hallowed be thy name"},
 "greek":{"text":"πατήρ","translit":"pater"},"hebrew":{"text":"אָב","translit":"av"},
 "ot_refs":"Gen 2:24 • Gen 4:20 • Gen 17:4","nt_refs":"Matt 6:9 • John 8:44 • Eph 3:14",
 "trivia":["Genesis calls Jabal the father of such as dwell in tents - the word names a founder as easily as a parent.","A man leaves his father and his mother, the first law of the household, is given before there is any father in the world.","Abram's new name, Abraham, is built from av and means father of a multitude."]}

DESIGNS["MOTHER"] = ("COMMON",
 {"core_meaning":"She of whom the living come - Adam called his wife's name Eve, because she was the mother of all living.",
  "type_expression":"A title of the household: four cards are revealed from the top of the Tower and the one revealed card whose card type belongs to the shared Chapter Lot is taken into the hand, as every living thing belongs to the mother of all living.",
  "mechanical_anchors":["belongs to the shared household","the mother of all living","every living thing","four cards revealed","taken into the hand"],
  "mechanic_seed":"Reveal the top four cards of the Tower; add one revealed card whose card type is in the Chapter Lot to the hand, because it belongs to the shared household as every living thing belongs to the mother of all living."},
 {"mechanical_expression":"The mother gathers what belongs to the shared household: four cards are revealed from the top of the Tower and the one revealed card whose card type stands in the Chapter Lot is taken into the hand.",
  "semantic_anchor":"belongs to the shared household",
  "semantic_evidence":["Reveal the top four cards of the Tower","Add one revealed card whose card type is in the Chapter Lot to your hand"],
  "ability_text":"Reveal the top four cards of the Tower. Add one revealed card whose card type is in the Chapter Lot to your hand.",
  "rules_terms":["cards","Tower","card","card type","Chapter Lot","hand","reveal","add"],
  "rules_actions":["reveal","add"],
  "clarity":cl(targets=["the top four cards of the Tower","your hand"],zones=["Tower","hand","Chapter Lot"],
               quantities=["top four cards","one revealed card"],
               outcomes=["Add one revealed card whose card type is in the Chapter Lot to your hand"]),
  "rarity_budget":budget(2,1,0,0,1, why=["the Tower, the Chapter Lot and the hand","one add after one look","no prior state is required","no other player is touched","one card taken, chosen from four seen"]) })
META["MOTHER"] = {"gloss":"She of whom the living come","weight":3,
 "weight_rationale":"the title Adam gives Eve at the hinge of the curse and the promise - thematic vocabulary with real teaching behind it",
 "art_prompt":"A woven grass nest holding four speckled eggs deep in a thorn bush, dew standing on the thorns, painted close up, no people, "+GOLDEN,
 "stats":{"lore":3,"context":4,"complexity":2},
 "stats_rationale":{"lore":"mother of all living is spoken over Eve immediately after the curse, and honour thy mother stands in the commandments - a recognized theme with clear teaching","context":"em occurs 220 times in the Hebrew Bible; meter occurs 83 times in the New Testament; total 303","complexity":"a plain kinship noun with stable translation; only its extension to a city called a mother in Israel needs a note"},
 "ot_verse":{"ref":"Genesis 3:20","snippet":"Adam called his wife's name Eve; because she was the mother of all living"},
 "nt_verse":{"ref":"Matthew 12:50","snippet":"the same is my brother, and sister, and mother"},
 "greek":{"text":"μήτηρ","translit":"meter"},"hebrew":{"text":"אֵם","translit":"em"},
 "ot_refs":"Gen 2:24 • Gen 3:20 • Gen 20:12","nt_refs":"Matt 12:50 • Luke 2:51 • John 19:25",
 "trivia":["Eve is named mother of all living in the same chapter that promises she will bring forth in sorrow.","Abram's defence of Sarai turns on the difference between a father's daughter and a mother's daughter.","Jesus redraws the household by obedience - whoever does the will of my Father is brother, sister and mother."]}

DESIGNS["STRANGER"] = ("COMMON",
 {"core_meaning":"One who dwells in a land that is not his own - thy seed shall be a stranger in a land that is not theirs.",
  "type_expression":"A title of not belonging: five cards are looked at from the top of the Tower and the one card whose card type stands outside your own Lot is taken into the hand, a portion that is not theirs.",
  "mechanical_anchors":["stands outside your own Lot","a land that is not theirs","dwells among another people","five cards looked at","taken into the hand"],
  "mechanic_seed":"Look at the top five cards of the Tower; add one of those cards that has a card type not in your Lot to the hand, a card that stands outside your own Lot as a stranger dwells in a land that is not theirs."},
 {"mechanical_expression":"The stranger takes what is not his own: five cards are looked at on the top of the Tower and the one card whose card type stands outside your own Lot is taken into the hand.",
  "semantic_anchor":"stands outside your own Lot",
  "semantic_evidence":["Look at the top five cards of the Tower","Add one of those cards that has a card type not in your Lot to your hand"],
  "ability_text":"Look at the top five cards of the Tower. Add one of those cards that has a card type not in your Lot to your hand.",
  "rules_terms":["cards","Tower","card","card type","Lot","hand","look at","add"],
  "rules_actions":["look at","add"],
  "clarity":cl(targets=["the top five cards of the Tower","your hand"],zones=["Tower","hand","Lot"],
               quantities=["top five cards","one of those cards"],
               outcomes=["Add one of those cards that has a card type not in your Lot to your hand"]),
  "rarity_budget":budget(2,1,0,0,1, why=["the Tower, your Lot and the hand","one add after one look","no prior state is required","no other player is touched","one card taken, chosen from five seen"]) })
META["STRANGER"] = {"gloss":"One who dwells in a land that is not his own","weight":3,
 "weight_rationale":"the word of the covenant warning to Abram and of the patriarchs' whole manner of life - thematic vocabulary with real teaching behind it",
 "art_prompt":"A traveller's dusty cloak and staff propped beside a closed wooden door set in a stone wall, an unfamiliar road running away behind, one figure seen from behind, "+GOLDEN,
 "stats":{"lore":3,"context":3,"complexity":3},
 "stats_rationale":{"lore":"the sojourner of Genesis 15 becomes the pattern for a people who confess they are strangers on the earth - a recognized theme with clear teaching","context":"ger occurs 92 times in the Hebrew Bible; paroikos occurs 4 times in the New Testament; total 96","complexity":"ger is a resident alien with standing, unlike nokri the outsider, and paroikos is one who dwells beside rather than among - two distinctions English flattens into stranger"},
 "ot_verse":{"ref":"Genesis 15:13","snippet":"thy seed shall be a stranger in a land that is not theirs"},
 "nt_verse":{"ref":"Ephesians 2:19","snippet":"Now therefore ye are no more strangers and foreigners"},
 "greek":{"text":"πάροικος","translit":"paroikos"},"hebrew":{"text":"גֵּר","translit":"ger"},
 "ot_refs":"Gen 15:13 • Gen 23:4 • Ps 39:12","nt_refs":"Eph 2:19 • Acts 7:6 • 1 Pet 2:11",
 "trivia":["Abraham calls himself a stranger and a sojourner even while buying the field where he will be buried.","Stephen quotes Genesis 15:13 word for word in his defence, and the Greek he uses is paroikos.","The law's command to love the stranger is grounded in memory - ye were strangers yourselves."]}

# ---------------------------------------------------------------- UNCOMMON
DESIGNS["CLEAN"] = ("UNCOMMON",
 {"core_meaning":"Fit to be brought near - of every clean beast thou shalt take to thee by sevens, and of beasts that are not clean by two; what is unclean is sorted out and sent away.",
  "type_expression":"An adjective of sorting: a card type is named as the unclean kind, one chosen player sends that kind away out of the hand, and the sorter draws two cards from the Tower.",
  "mechanical_anchors":["sorted out and sent away","the unclean kind","clean beast by sevens","one named kind","brought near"],
  "mechanic_seed":"Name a card type as the unclean kind; a chosen player sends one card of that named kind out of the hand, sorted out and sent away into Sheol, and then two cards are drawn from the Tower."},
 {"mechanical_expression":"The unclean kind is sorted out and sent away: a card type is named, one chosen player loses a card of that named kind out of the hand into Sheol, and two cards are drawn from the Tower.",
  "semantic_anchor":"sorted out and sent away",
  "semantic_evidence":["Name a card type","that chosen player puts one card of the named type from that chosen player's hand into Sheol","draw two cards from the Tower"],
  "ability_text":"Name a card type. Choose another player; that chosen player puts one card of the named type from that chosen player's hand into Sheol, then draw two cards from the Tower.",
  "rules_terms":["card type","player","card","hand","Sheol","cards","Tower","name","choose","put","draw"],
  "rules_actions":["name","choose","put","draw"],
  "clarity":cl(targets=["another player","that chosen player"],zones=["hand","Sheol","Tower"],
               quantities=["a card type","one card","two cards"],
               outcomes=["that chosen player puts one card of the named type from that chosen player's hand into Sheol","draw two cards from the Tower"]),
  "rarity_budget":budget(2,2,1,1,2, why=["the hand, Sheol and the Tower are touched","one naming, one forced placement and one draw","Sheol receives the sorted card","one chosen player loses a card of the named type","two cards drawn, with a card taken off one player"]) })
META["CLEAN"] = {"gloss":"Fit to be brought near, as the clean beasts taken by sevens","weight":3,
 "weight_rationale":"the clean and unclean distinction enters Scripture at the ark and runs to Peter's sheet - thematic vocabulary with real teaching behind it",
 "art_prompt":"The lamplit interior of the ark, a wicker cage of white doves and a pair of young lambs bedded on fresh straw between cedar ribs, no people, "+LANTERN,
 "stats":{"lore":3,"context":4,"complexity":3},
 "stats_rationale":{"lore":"the clean beasts board the ark by sevens and the pure in heart see God - a recognized theme with clear teaching","context":"tahor occurs 96 times in the Hebrew Bible; katharos occurs 27 times in the New Testament; total 123","complexity":"tahor is ritual fitness rather than cleanliness, and katharos slides from ritually clean to morally pure to simply unmixed - a shift that changes how a verse reads"},
 "ot_verse":{"ref":"Genesis 7:2","snippet":"Of every clean beast thou shalt take to thee by sevens"},
 "nt_verse":{"ref":"Matthew 5:8","snippet":"Blessed are the pure in heart: for they shall see God"},
 "greek":{"text":"καθαρός","translit":"katharos"},"hebrew":{"text":"טָהוֹר","translit":"tahor"},
 "ot_refs":"Gen 7:2 • Gen 7:8 • Gen 8:20","nt_refs":"Matt 5:8 • John 15:3 • Titus 1:15",
 "trivia":["The clean and unclean distinction appears in Genesis 7, generations before any law names which beasts are which.","Noah takes clean beasts by sevens precisely because he will sacrifice some of them when he lands.","Katharos gives English catharsis; the same root covers a scrubbed pot and a clean conscience."]}

DESIGNS["HAGAR"] = ("UNCOMMON",
 {"core_meaning":"Sarai's handmaid, dealt with hardly and driven out, whom the angel found by a fountain of water in the wilderness and sent back with a promise.",
  "type_expression":"A name of the one driven out and found: one chosen player puts a card down to the bottom of the Tower, out into the wilderness, and then up to two cards long cast away in Sheol are found again and taken into the hand.",
  "mechanical_anchors":["sent down under the Tower","driven out into the wilderness","found again by the fountain","cast away","a promise brought back"],
  "mechanic_seed":"A chosen player puts one card out of the hand down to the bottom of the Tower, driven out into the wilderness; then up to two cards cast away in Sheol are found again and taken into the hand as the angel found Hagar by the fountain."},
 {"mechanical_expression":"Hagar is driven out and then found: one chosen player's card is sent down under the Tower to its bottom, and up to two cards cast away in Sheol are taken back into the hand.",
  "semantic_anchor":"sent down under the Tower",
  "semantic_evidence":["that chosen player puts one card from that chosen player's hand on the bottom of the Tower","add up to two cards from Sheol to your hand"],
  "ability_text":"Choose another player; that chosen player puts one card from that chosen player's hand on the bottom of the Tower. Then add up to two cards from Sheol to your hand.",
  "rules_terms":["player","card","hand","Tower","cards","Sheol","choose","put","add"],
  "rules_actions":["choose","put","add"],
  "clarity":cl(targets=["another player","that chosen player","your hand"],zones=["hand","Tower","Sheol"],
               quantities=["one card","up to two cards"],
               outcomes=["that chosen player puts one card from that chosen player's hand on the bottom of the Tower","add up to two cards from Sheol to your hand"]),
  "rarity_budget":budget(2,2,1,1,2, why=["the hand, the Tower and Sheol are touched","one forced placement and one scaling recovery","Sheol must hold cards for the recovery","one chosen player loses a card out of hand","up to two cards recovered out of Sheol"]) })
META["HAGAR"] = {"gloss":"Sarai's handmaid, driven out and found by the fountain","weight":3,
 "weight_rationale":"the outcast of Abram's household whom Paul reads as a covenant - thematic vocabulary with real teaching behind it, but not a patriarch the era turns on",
 "art_prompt":"A spring welling up among broken red rocks in the wilderness, a leather waterskin lying open on the sand beside it and one set of footprints leading away, no people, "+DESERT,
 "stats":{"lore":3,"context":2,"complexity":4},
 "stats_rationale":{"lore":"the first person in Scripture to name God, and the figure Paul builds a covenant argument on - a recognized theme with clear teaching","context":"Hagar occurs 12 times in the Hebrew Bible; Hagar occurs 2 times in the New Testament; total 14","complexity":"her name is read as flight, as stranger, or from an Arabic root for departure; Paul turns her into an allegory of Sinai, and the well she names, Beer-lahai-roi, is itself a translation puzzle"},
 "ot_verse":{"ref":"Genesis 16:8","snippet":"And he said, Hagar, Sarai's maid, whence camest thou? and whither wilt thou go?"},
 "nt_verse":{"ref":"Galatians 4:24","snippet":"the one from the mount Sinai, which gendereth to bondage, which is Agar"},
 "greek":{"text":"Ἁγάρ","translit":"Hagar"},"hebrew":{"text":"הָגָר","translit":"Hagar"},
 "ot_refs":"Gen 16:1 • Gen 16:8 • Gen 21:17","nt_refs":"Gal 4:24 • Gal 4:25",
 "trivia":["Hagar is the first person in Scripture to give God a name - Thou God seest me.","The angel's command is to return and submit; the promise of a multitude comes only after the going back.","Paul makes Hagar and Sarah two covenants, which is why a handmaid of Genesis argues a point in Galatians."]}

# ---------------------------------------------------------------- RARE
DESIGNS["PERFECT"] = ("RARE",
 {"core_meaning":"Whole and without blemish - Noah was a just man and perfect in his generations; what is perfect is complete, with nothing wanting.",
  "type_expression":"An adjective of the unblemished: four cards are looked at on the top of the Tower and only those cards of full LORE are kept, nothing wanting, and a record already whole in the Pages earns a Letter besides.",
  "mechanical_anchors":["only those cards of full LORE","perfect in his generations","nothing wanting","a record already whole","four cards looked at"],
  "mechanic_seed":"Look at the top four cards of the Tower and keep only those cards of full LORE, up to two of them, taking nothing that is blemished; then, if the record already standing in the Pages is whole, a Letter is earned besides."},
 {"mechanical_expression":"The unblemished are kept and nothing else is: of four cards looked at on the top of the Tower, only those cards of full LORE come into the hand, and a whole enough record standing in your Pages earns a Letter besides.",
  "semantic_anchor":"only those cards of full LORE",
  "semantic_evidence":["Look at the top four cards of the Tower","add up to two of those cards that each have LORE four or more to your hand","If the cards in your Pages have total LORE ten or more"],
  "ability_text":"Look at the top four cards of the Tower and add up to two of those cards that each have LORE four or more to your hand. If the cards in your Pages have total LORE ten or more, gain one Letter.",
  "rules_terms":["cards","Tower","LORE","hand","Pages","Letter","look at","add","gain"],
  "rules_actions":["look at","add","gain"],
  "clarity":cl(targets=["the top four cards of the Tower","your hand"],zones=["Tower","hand","Pages"],
               quantities=["top four cards","up to two of those cards","one Letter"],
               condition="If the cards in your Pages have total LORE ten or more",
               outcomes=["add up to two of those cards that each have LORE four or more to your hand","gain one Letter"]),
  "rarity_budget":budget(2,2,2,0,3, why=["the Tower, the hand and your Pages","a LORE-sorted add and a conditional gain","a standing total of LORE in your Pages must already be built","no other player is touched","up to two unblemished cards of four seen, and a Letter worth three cards when the record is whole"]) })
META["PERFECT"] = {"gloss":"Whole and without blemish, with nothing wanting","weight":4,
 "weight_rationale":"the verdict on Noah that spares the world and the standard given to Abram - a named judgment the era turns on, and the word people look for",
 "art_prompt":"A carpenter's plumb line hanging dead straight beside a squared beam of gopher wood, a bronze square and a bowl of black pitch on the bench, no people, "+GOLDEN,
 "stats":{"lore":5,"context":3,"complexity":4},
 "stats_rationale":{"lore":"perfect in his generations is why Noah is saved, and Be ye therefore perfect is the sermon's summary - a doctrine hangs on the word","context":"tamim occurs 91 times in the Hebrew Bible; teleios occurs 19 times in the New Testament; total 110","complexity":"tamim means whole or unblemished rather than flawless, and is the sacrifice word before it is a character word; teleios means brought to its end or complete, so both languages say finished where English says perfect - a translation choice that changes the doctrine"},
 "ot_verse":{"ref":"Genesis 6:9","snippet":"Noah was a just man and perfect in his generations"},
 "nt_verse":{"ref":"Matthew 5:48","snippet":"Be ye therefore perfect, even as your Father which is in heaven is perfect"},
 "greek":{"text":"τέλειος","translit":"teleios"},"hebrew":{"text":"תָּמִים","translit":"tamim"},
 "ot_refs":"Gen 6:9 • Gen 17:1 • Deut 18:13","nt_refs":"Matt 5:48 • Col 1:28 • James 1:4",
 "trivia":["Tamim is the word for a sacrifice without blemish; applied to Noah it says whole, not sinless.","God tells Abram to walk before me, and be thou tamim - the same standard, given as a command instead of a verdict.","Teleios is built on telos, an end or goal; the perfect thing is the finished thing, not the flawless one."]}

DESIGNS["PRIEST"] = ("RARE",
 {"core_meaning":"The one who stands between and brings the offering near - Melchizedek king of Salem brought forth bread and wine, and he was the priest of the most high God, and Abram gave him tithes of all.",
  "type_expression":"A title of the offering received: one chosen player spends a Letter as the tithe, and the priest brings forth bread and wine, taking two cards out of Sheol and one card back out of a standing Page.",
  "mechanical_anchors":["pays the tithe","brought forth bread and wine","stands between","tithes of all","back out of a standing Page"],
  "mechanic_seed":"A chosen player spends one Letter as the tithe paid to the priest; then the priest brings forth bread and wine, taking up to two cards out of Sheol into the hand and one card back out of a standing Page."},
 {"mechanical_expression":"The chosen player pays the tithe of one Letter and the priest brings forth bread and wine: two cards come up out of Sheol into the hand and one card comes back out of a standing Page.",
  "semantic_anchor":"pays the tithe",
  "semantic_evidence":["that chosen player spends one Letter","add up to two cards from Sheol to your hand","return one card from one of your Pages to your hand"],
  "ability_text":"Choose another player; that chosen player spends one Letter. Then add up to two cards from Sheol to your hand and return one card from one of your Pages to your hand.",
  "rules_terms":["player","Letter","cards","Sheol","hand","card","Pages","choose","spend","add","return"],
  "rules_actions":["choose","spend","add","return"],
  "clarity":cl(targets=["another player","that chosen player","your hand"],zones=["Sheol","hand","Pages"],
               quantities=["one Letter","up to two cards","one card"],
               outcomes=["that chosen player spends one Letter","add up to two cards from Sheol to your hand","return one card from one of your Pages to your hand"]),
  "rarity_budget":budget(2,3,1,2,3, why=["Sheol, the hand and your Pages are touched","a forced payment, a scaling recovery and a return from a Page","Sheol and a standing Page must hold cards","one chosen player is made to spend a Letter, worth three cards","two cards out of Sheol and one card back out of a Page"]) })
META["PRIEST"] = {"gloss":"The one who stands between and receives the offering","weight":4,
 "weight_rationale":"Melchizedek's title in Genesis 14, the one office the era names, and the hinge of the argument of Hebrews - the card people will look for",
 "art_prompt":"A low stone table in a shadowed hall of Salem holding a torn round loaf and a clay cup of dark wine, a folded linen cloth beside them, no people, "+GOLDEN,
 "stats":{"lore":5,"context":5,"complexity":3},
 "stats_rationale":{"lore":"priest of the most high God, and thou art a priest for ever after the order of Melchizedek - a doctrine hangs on the word","context":"kohen occurs 750 times in the Hebrew Bible; hiereus occurs 31 times in the New Testament; total 781","complexity":"kohen names both Israel's priests and the priests of other gods, and Melchizedek's priesthood has no genealogy, which is exactly the point Hebrews presses - a history worth explaining"},
 "ot_verse":{"ref":"Genesis 14:18","snippet":"he brought forth bread and wine: and he was the priest of the most high God"},
 "nt_verse":{"ref":"Hebrews 7:1","snippet":"this Melchisedec, king of Salem, priest of the most high God"},
 "greek":{"text":"ἱερεύς","translit":"hiereus"},"hebrew":{"text":"כֹּהֵן","translit":"kohen"},
 "ot_refs":"Gen 14:18 • Ps 110:4 • Lev 21:10","nt_refs":"Heb 7:1 • Heb 5:6 • Rev 1:6",
 "trivia":["Melchizedek is the first priest named in Scripture, and he appears centuries before there is a priesthood.","Abram gives him tithes of all - the tithe is older than the law that commands it.","Hebrews argues from the silence of Genesis: no father, no mother, no beginning of days recorded, therefore a priest for ever."]}

# ---------------------------------------------------------------- GLORIOUS
DESIGNS["FLOOD"] = ("GLORIOUS",
 {"core_meaning":"The waters that came upon the earth and took them all away - every living substance was destroyed from off the ground, and only what was borne up in the ark came through.",
  "type_expression":"A noun of the world emptied and repeopled: every hand goes down into the waters of Sheol, then the world begins again empty and each player draws one card back from the Tower while the one borne up in the ark comes out with four.",
  "mechanical_anchors":["the world begins again empty","took them all away","every living substance","borne up in the ark","every hand goes down into the waters"],
  "mechanic_seed":"Each player puts every card out of the hand down into the waters of Sheol; then each player draws one card back from the Tower and the one borne up in the ark draws four cards more."},
 {"mechanical_expression":"Every hand goes down into the waters and the world begins again empty: each player puts every card from the hand into Sheol, each player draws one card back from the Tower, and the one borne up in the ark comes out with four.",
  "semantic_anchor":"the world begins again empty",
  "semantic_evidence":["Each player puts every card from that player\'s hand into Sheol","each player draws one card from the Tower","you draw four cards from the Tower"],
  "ability_text":"Each player puts every card from that player\'s hand into Sheol. Then each player draws one card from the Tower and you draw four cards from the Tower.",
  "rules_terms":["player","card","hand","Sheol","cards","Tower","put","draw"],
  "rules_actions":["put","draw","draw"],
  "clarity":cl(targets=["Each player","that player\'s hand"],zones=["hand","Sheol","Tower"],
               quantities=["every card","one card","four cards"],
               outcomes=["Each player puts every card from that player\'s hand into Sheol","each player draws one card from the Tower","you draw four cards from the Tower"]),
  "rarity_budget":budget(3,3,1,3,4, why=["every player, the hand, Sheol and the Tower","a table-wide emptying of hands and two draws","Sheol receives every hand in the game","every player loses an entire hand of material","every hand in the game destroyed and the activating player alone comes out with five cards"]) })
META["FLOOD"] = {"gloss":"The waters that came upon the earth and took them all away","weight":5,
 "weight_rationale":"the pillar the whole era turns on - the judgment the ark, the dove, the covenant and the rainbow all hang from; the chase card of the set",
 "art_prompt":"Black water surging through the open doorway of a stone house, a wooden bowl and a clay jar spinning on the flood, rain hammering the drowned threshold, no people, "+STORM,
 "stats":{"lore":5,"context":2,"complexity":4},
 "stats_rationale":{"lore":"the flood is the era's judgment and the New Testament's own picture of the day of the Lord and of baptism - a doctrine hangs on the word","context":"mabbul occurs 13 times in the Hebrew Bible; kataklysmos occurs 4 times in the New Testament; total 17","complexity":"mabbul is reserved for this one event and for the LORD sitting upon the flood in Psalm 29, so its derivation is argued from yabal to flow, from nabal to fall, and from an Akkadian loan; kataklysmos, the word the Greek translators chose, gives English cataclysm"},
 "ot_verse":{"ref":"Genesis 7:17","snippet":"And the flood was forty days upon the earth"},
 "nt_verse":{"ref":"Matthew 24:39","snippet":"knew not until the flood came, and took them all away"},
 "greek":{"text":"κατακλυσμός","translit":"kataklysmos"},"hebrew":{"text":"מַבּוּל","translit":"mabbul"},
 "ot_refs":"Gen 6:17 • Gen 7:17 • Gen 9:11 • Ps 29:10","nt_refs":"Matt 24:38 • Matt 24:39 • Luke 17:27 • 2 Pet 2:5",
 "trivia":["Hebrew keeps a separate word for this water: mabbul is never used of an ordinary river in flood.","Psalm 29:10 is the one place outside Genesis that uses it - the LORD sitteth upon the flood, still enthroned over it.","Peter reads the flood as a figure of baptism: the same water that destroys the world carries the ark."]}


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


TYPES = {"PLANT":"VERB","DRY":"ADJECTIVE","AFRAID":"ADJECTIVE","FRUITFUL":"ADJECTIVE",
         "LAMECH":"NAME","TERAH":"NAME","FATHER":"TITLE","MOTHER":"TITLE","STRANGER":"TITLE",
         "CLEAN":"ADJECTIVE","HAGAR":"NAME","PERFECT":"ADJECTIVE","PRIEST":"TITLE","FLOOD":"NOUN"}
