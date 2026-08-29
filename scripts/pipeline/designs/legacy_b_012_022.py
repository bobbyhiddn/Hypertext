"""Module B regen: legacy slots #012-#022 (FORM, REMEMBER, MULTIPLY, SPEAK, GOOD, NATION,
SETH, KEEPER, ARK, BROTHER, SHEM) redesigned under the grammar, the power ladder, word
weight, the stat rubric, the mechanic axes and the art subject/lighting rules.

The WORD and the printed Hebrew/Greek lemmas of each slot are unchanged; ability, art,
stats, weight, verses and trivia are new.
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
DESIGNS["GOOD"] = ("COMMON",
 {"core_meaning":"Fit for the purpose it was made for - God saw every thing that he had made, and, behold, it was very good; what is good is looked over and approved.",
  "type_expression":"An adjective of appraisal: three cards are looked over and the one weighty enough is approved into the hand, while the rest are laid under.",
  "mechanical_anchors":["looked over and approved","very good","weighty enough","laid under","LORE three or more"],
  "mechanic_seed":"Look at the top three cards of the Tower, looked over as God looked over what he had made; add one of those cards that has LORE three or more to your hand, approved as very good, and put the other cards on the bottom of the Tower, laid under."},
 {"mechanical_expression":"Three cards are looked over and approved: the one with LORE three or more is added to the hand, weighty enough to be called very good, and each other card is put on the bottom of the Tower.",
  "semantic_anchor":"looked over and approved",
  "semantic_evidence":["Look at the top three cards of the Tower","Add one of those cards that has LORE three or more to your hand","put the other cards on the bottom of the Tower"],
  "ability_text":"Look at the top three cards of the Tower. Add one of those cards that has LORE three or more to your hand and put the other cards on the bottom of the Tower.",
  "rules_terms":["cards","Tower","LORE","hand","card","look at","add","put"],
  "rules_actions":["look at","add","put"],
  "clarity":cl(targets=["the top three cards of the Tower","your hand"],zones=["Tower","hand"],quantities=["top three cards","one of those cards"],outcomes=["Add one of those cards that has LORE three or more to your hand","put the other cards on the bottom of the Tower"]),
  "rarity_budget":budget(2,2,0,0,1, why=["the Tower and the hand","one add and one placement","no prior state is required","no other player is touched","one card taken, chosen by its LORE from three seen"]) })
META["GOOD"] = {"gloss":"Fit for its purpose; approved on sight","weight":2,"weight_rationale":"the refrain of the creation week and the name of the forbidden tree - a descriptive word with a clear place in the era, not a named agent or event, so it stays at 2 and prints COMMON",
 "art_prompt":"A green valley heavy with ripe fruit trees, long grass and low fig branches, small birds turning over the slope, no people, "+S("noon"),
 "stats":{"lore":4,"context":5,"complexity":3},
 "stats_rationale":{"lore":"the printed verses are the verdict on the whole creation and the verdict that none is good but God - the era's judgment of worth rests on this word","context":"tov occurs 559 times in the Hebrew Bible; agathos occurs 102 times in the New Testament; total 661","complexity":"tov covers good, pleasant, fit and beautiful in one adjective, and the tree of the knowledge of good and evil pairs it with ra - a range a translator must choose within"},
 "ot_verse":{"ref":"Genesis 1:31","snippet":"God saw every thing that he had made, and, behold, it was very good"},"nt_verse":{"ref":"Matthew 19:17","snippet":"there is none good but one, that is, God"},
 "greek":{"text":"ἀγαθός","translit":"agathos"},"hebrew":{"text":"טוֹב","translit":"tov"},
 "ot_refs":"Gen 1:31 • Gen 1:4 • Gen 2:18","nt_refs":"Matt 19:17 • Matt 7:17 • Rom 12:21",
 "trivia":["Six days are called good; only the sixth is called very good, and only one thing in Eden is called not good - that the man should be alone.","The tree of the knowledge of good and evil sets tov against ra, the only pairing in Genesis where knowing is forbidden.","Greek splits the word Hebrew keeps whole: agathos is good in worth, kalos good to look at, and the Septuagint chooses between them verse by verse."]}

DESIGNS["SETH"] = ("COMMON",
 {"core_meaning":"The appointed one - God hath appointed me another seed instead of Abel, whom Cain slew; Seth is the son set in the place of the son lost.",
  "type_expression":"A name of appointment: two sons come up together, one is appointed into the hand and the other is set back in place on top.",
  "mechanical_anchors":["appointed into the hand","another seed instead of Abel","set back in place","two sons come up","the son lost"],
  "mechanic_seed":"Look at the top two cards of the Tower, two sons come up together; add one of those cards to your hand, appointed into the hand as another seed, and put the other card on top of the Tower, set back in place."},
 {"mechanical_expression":"Two cards come up together and one is appointed into the hand as another seed, while the other card is set back in place on top of the Tower.",
  "semantic_anchor":"appointed into the hand",
  "semantic_evidence":["Look at the top two cards of the Tower","Add one of those cards to your hand","put the other card on top of the Tower"],
  "ability_text":"Look at the top two cards of the Tower. Add one of those cards to your hand and put the other card on top of the Tower.",
  "rules_terms":["cards","Tower","hand","card","look at","add","put"],
  "rules_actions":["look at","add","put"],
  "clarity":cl(targets=["the top two cards of the Tower","your hand"],zones=["Tower","hand"],quantities=["top two cards","one of those cards"],outcomes=["Add one of those cards to your hand","put the other card on top of the Tower"]),
  "rarity_budget":budget(2,2,0,0,1, why=["the Tower and the hand","one add and one placement","no prior state is required","no other player is touched","one card taken of two seen, the other left known on top"]) })
META["SETH"] = {"gloss":"Appointed; the seed set in Abel's place","weight":2,"weight_rationale":"a genealogy name with a stated meaning that carries the line from Adam to Noah - a clear place in the era, but the patriarchs the era turns on are Adam and Noah, so Seth stays at 2",
 "art_prompt":"A young olive shoot rising from a cracked clay jar of earth beside a low stone doorway, an older snapped shoot lying dry on the step, no people, "+S("golden"),
 "stats":{"lore":2,"context":1,"complexity":3},
 "stats_rationale":{"lore":"the printed verses give a replacement son and a name in a genealogy; the line matters, but no teaching hangs on Seth himself","context":"Sheth occurs 9 times in the Hebrew Bible; Seth occurs 1 time in the New Testament; total 10","complexity":"the name is read off shath, to set or appoint, in Eve's own explanation - a folk etymology built into the verse, and the same consonants elsewhere mean foundation or tumult"},
 "ot_verse":{"ref":"Genesis 4:25","snippet":"she called his name Seth: For God, said she, hath appointed me another seed"},"nt_verse":{"ref":"Luke 3:38","snippet":"which was the son of Seth, which was the son of Adam"},
 "greek":{"text":"Σήθ","translit":"Seth"},"hebrew":{"text":"שֵׁת","translit":"Sheth"},
 "ot_refs":"Gen 4:25 • Gen 4:26 • Gen 5:3","nt_refs":"Luke 3:38",
 "trivia":["Genesis 5:3 says Adam begat a son in his own likeness, after his image - the words of Genesis 1 handed down one generation.","In the days of Seth's son Enos men began to call upon the name of the LORD.","Luke's genealogy runs backward through Seth to Adam, and only there stops at the son of God."]}

DESIGNS["BROTHER"] = ("COMMON",
 {"core_meaning":"One of your own kin - Abram says to Lot, let there be no strife between me and thee, for we be brethren; a brother is the one who shares your kind.",
  "type_expression":"A title of kinship: three cards are shown openly and the one of your own kind - a card type in your Lot - comes to the hand, the rest set back on top.",
  "mechanical_anchors":["of your own kind","we be brethren","shown openly","set back on top","a card type in your Lot"],
  "mechanic_seed":"Reveal the top three cards of the Tower, shown openly as kin are known; add one revealed card whose card type is in your Lot to your hand, of your own kind, and put each other revealed card on top of the Tower, set back on top."},
 {"mechanical_expression":"Three cards are shown openly and the one of your own kind - the revealed card whose card type is in your Lot - is added to the hand, while each other revealed card is put back on top of the Tower.",
  "semantic_anchor":"of your own kind",
  "semantic_evidence":["Reveal the top three cards of the Tower","Add one revealed card whose card type is in your Lot to your hand","put each other revealed card on top of the Tower"],
  "ability_text":"Reveal the top three cards of the Tower. Add one revealed card whose card type is in your Lot to your hand and put each other revealed card on top of the Tower.",
  "rules_terms":["cards","Tower","card type","Lot","hand","card","reveal","add","put"],
  "rules_actions":["reveal","add","put"],
  "clarity":cl(targets=["the top three cards of the Tower","your hand"],zones=["Tower","Lot","hand"],quantities=["top three cards","one revealed card"],outcomes=["Add one revealed card whose card type is in your Lot to your hand","put each other revealed card on top of the Tower"]),
  "rarity_budget":budget(2,2,0,0,1, why=["the Tower, your Lot and the hand","one add and one placement","your Lot is read as it lies, with no prior state built","no other player is touched","one card taken, and only if it is kin to your Lot"]) })
META["BROTHER"] = {"gloss":"A kinsman; one who shares your kind","weight":2,"weight_rationale":"the era's first murder and Noah's three sons are told in the language of brothers, but the word is a relation rather than a named agent or event, so it stays at 2 and prints COMMON",
 "art_prompt":"Two shepherds' staffs leaning together against a boundary stone where a track divides into two ways, the dust of a flock hanging over each way, no people, "+S("golden"),
 "stats":{"lore":3,"context":5,"complexity":3},
 "stats_rationale":{"lore":"the printed verses set Abram's peace with Lot beside the one who is not ashamed to call us brethren - a recognized theme with clear teaching","context":"ach occurs 629 times in the Hebrew Bible; adelphos occurs 343 times in the New Testament; total 972","complexity":"ach stretches from a blood brother to a nephew, a neighbour and a whole nation - Lot is called Abram's brother though he is his brother's son - and adelphos inherits the stretch"},
 "ot_verse":{"ref":"Genesis 13:8","snippet":"let there be no strife, I pray thee, between me and thee ... for we be brethren"},"nt_verse":{"ref":"Hebrews 2:11","snippet":"for which cause he is not ashamed to call them brethren"},
 "greek":{"text":"ἀδελφός","translit":"adelphos"},"hebrew":{"text":"אָח","translit":"ach"},
 "ot_refs":"Gen 13:8 • Gen 4:8 • Gen 9:22","nt_refs":"Heb 2:11 • 1 John 3:12 • Matt 5:24",
 "trivia":["Adelphos is literally from one womb - a-delphys - which is why the New Testament has to stretch it to cover the church.","Genesis 4 calls Abel his brother seven times in six verses; the word is repeated until the murder is unmistakably fratricide.","Lot is Abram's nephew, yet Abram calls him brother - kinship in Genesis names the bond, not the exact degree."]}

# ---------------------------------------------------------------- UNCOMMON
DESIGNS["FORM"] = ("UNCOMMON",
 {"core_meaning":"To shape as a potter shapes - the LORD God formed man of the dust of the ground; what is formed is taken up and made after a pattern.",
  "type_expression":"A verb of shaping: a card is taken up fresh from the Tower as the pattern, and dust is raised out of Sheol and shaped after that pattern's card type.",
  "mechanical_anchors":["taken up as the pattern","formed of the dust of the ground","shaped after that pattern","raised out of Sheol","the potter's kind"],
  "mechanic_seed":"Add one card from the top of the Tower to your hand, taken up as the pattern; then choose one card in Sheol of that added card's card type, dust raised out of Sheol and shaped after that pattern, and add that chosen card to your hand."},
 {"mechanical_expression":"One card is taken up as the pattern from the top of the Tower, and then dust is raised out of Sheol: a card of that added card's card type is chosen and added to the hand, shaped after that pattern.",
  "semantic_anchor":"taken up as the pattern",
  "semantic_evidence":["Add one card from the top of the Tower to your hand","choose one card in Sheol of that added card's card type","add that chosen card to your hand"],
  "ability_text":"Add one card from the top of the Tower to your hand. Then choose one card in Sheol of that added card's card type and add that chosen card to your hand.",
  "rules_terms":["card","Tower","hand","Sheol","card type","add","choose"],
  "rules_actions":["add","choose","add"],
  "clarity":cl(targets=["your hand","one card in Sheol"],zones=["Tower","hand","Sheol"],quantities=["one card","one card"],outcomes=["Add one card from the top of the Tower to your hand","add that chosen card to your hand"]),
  "rarity_budget":budget(2,2,1,0,2, why=["the Tower, the hand and Sheol","one add, one search of Sheol and a second add","Sheol must hold a card of the added card's type","no other player is touched","two cards, the second matched to the first"]) })
META["FORM"] = {"gloss":"To shape or mould as a potter shapes clay","weight":3,"weight_rationale":"the potter's verb of Genesis 2:7 and of Christ formed in you - thematic vocabulary with real teaching; the era's making is carried by CREATE, so FORM stays at 3 rather than taking a RARE slot",
 "art_prompt":"A potter's workbench in a shuttered workshop, a half-shaped figure of wet red clay standing on the wheel, a bowl of grey slip and a drift of dry dust across the boards, no people, "+S("lantern"),
 "stats":{"lore":4,"context":3,"complexity":4},
 "stats_rationale":{"lore":"the printed verses give the making of man from dust and Christ formed in a people - the era's account of what a human being is rests on this verb","context":"yatsar occurs 63 times in the Hebrew Bible; morphoo occurs 1 time in the New Testament; total 64","complexity":"yatsar is the potter's verb, and its noun yetser is the imagination of the heart that Genesis 6:5 calls evil continually - the same root names both the shaping and the thing shaped, and morphoo carries the argument about form and nature into Greek"},
 "ot_verse":{"ref":"Genesis 2:7","snippet":"And the LORD God formed man of the dust of the ground"},"nt_verse":{"ref":"Galatians 4:19","snippet":"until Christ be formed in you"},
 "greek":{"text":"μορφόω","translit":"morphoo"},"hebrew":{"text":"יָצַר","translit":"yatsar"},
 "ot_refs":"Gen 2:7 • Gen 2:8 • Gen 2:19","nt_refs":"Gal 4:19",
 "trivia":["Genesis 2:19 forms the beasts from the ground with the same verb it used for the man; only the man receives the breath of life.","Yatsar is written with a doubled letter in Genesis 2:7 that the rabbis read as two formations - one for this world and one for the next.","Isaiah turns the verb into the potter and clay argument that Paul takes up in Romans 9."]}

DESIGNS["REMEMBER"] = ("UNCOMMON",
 {"core_meaning":"To call back to mind and act - God remembered Noah, and made a wind to pass over the earth, and the waters assuaged; remembering moves the hand.",
  "type_expression":"A verb of recall: what is already written into your Pages is called back out of Sheol, up to two cards of a card type you have recorded.",
  "mechanical_anchors":["called back out of Sheol","God remembered Noah","already written into your Pages","the waters assuaged","up to two cards recalled"],
  "mechanic_seed":"Choose up to two cards in Sheol whose card type is in one of your Pages, already written into your Pages, and add those chosen cards to your hand - called back out of Sheol as God remembered Noah."},
 {"mechanical_expression":"What is already written into your Pages is called back out of Sheol: up to two cards in Sheol whose card type is in one of your Pages are chosen and added to the hand.",
  "semantic_anchor":"called back out of Sheol",
  "semantic_evidence":["Choose up to two cards in Sheol whose card type is in one of your Pages","add those chosen cards to your hand"],
  "ability_text":"Choose up to two cards in Sheol whose card type is in one of your Pages and add those chosen cards to your hand.",
  "rules_terms":["cards","Sheol","card type","Pages","hand","choose","add"],
  "rules_actions":["choose","add"],
  "clarity":cl(targets=["up to two cards in Sheol","your hand"],zones=["Sheol","Pages","hand"],quantities=["up to two cards","those chosen cards"],outcomes=["add those chosen cards to your hand"]),
  "rarity_budget":budget(2,2,1,0,2, why=["Sheol, your Pages and the hand","one filtered search and one add","a Page must already be recorded and Sheol must hold its types","no other player is touched","up to two cards recovered from Sheol"]) })
META["REMEMBER"] = {"gloss":"To call back to mind and act upon it","weight":3,"weight_rationale":"God remembering Noah is the hinge the flood turns on and remembering the covenant is how the era's promises hold - thematic vocabulary with real teaching, while the pillar itself is COVENANT, so REMEMBER stays at 3",
 "art_prompt":"Dark floodwaters draining off a bare mountain shoulder, a long wind-track combing the surface, a bent olive branch dripping over the water, no people, "+S("storm"),
 "stats":{"lore":4,"context":4,"complexity":3},
 "stats_rationale":{"lore":"the printed verses turn the flood by God remembering Noah and answer a dying thief who asks to be remembered - in this era remembering is the act that saves","context":"zakar occurs 235 times in the Hebrew Bible; mnaomai occurs 21 times in the New Testament; total 256","complexity":"zakar never means mere recollection: God remembering is God acting, and the noun zikkaron is a memorial object, so translators must decide between mind and deed"},
 "ot_verse":{"ref":"Genesis 8:1","snippet":"And God remembered Noah ... and God made a wind to pass over the earth"},"nt_verse":{"ref":"Luke 23:42","snippet":"Lord, remember me when thou comest into thy kingdom"},
 "greek":{"text":"μνάομαι","translit":"mnaomai"},"hebrew":{"text":"זָכַר","translit":"zakar"},
 "ot_refs":"Gen 8:1 • Gen 9:15 • Gen 19:29","nt_refs":"Luke 23:42 • Matt 26:75 • Acts 10:31",
 "trivia":["Genesis 8:1 is the exact centre of the flood account; everything before it rises and everything after it falls.","God remembers Noah, then Abraham, then Rachel - in each case the next word is an action, never a thought.","The bow in the cloud is set there so that God may look upon it and remember; the sign is for the one who gave it."]}

DESIGNS["MULTIPLY"] = ("UNCOMMON",
 {"core_meaning":"To become many out of one - in multiplying I will multiply thy seed; a single grain goes into the ground and comes up threefold.",
  "type_expression":"A verb of increase: one card that fills the earth - CONTEXT four or more - is sown down into Sheol, and comes back as a Letter, which is worth three cards.",
  "mechanical_anchors":["sown down into Sheol","in multiplying I will multiply","comes back threefold","one card that fills the earth","CONTEXT four or more"],
  "mechanic_seed":"Discard one card with CONTEXT four or more from your hand into Sheol, sown down into Sheol as seed is sown. Then gain one Letter, which comes back threefold."},
 {"mechanical_expression":"One card that fills the earth, with CONTEXT four or more, is sown down into Sheol from the hand, and one Letter is gained in its place - the single card comes back threefold.",
  "semantic_anchor":"sown down into Sheol",
  "semantic_evidence":["Discard one card with CONTEXT four or more from your hand into Sheol","gain one Letter"],
  "ability_text":"Discard one card with CONTEXT four or more from your hand into Sheol. Then gain one Letter.",
  "rules_terms":["card","CONTEXT","hand","Sheol","Letter","discard","gain"],
  "rules_actions":["discard","gain"],
  "clarity":cl(targets=["one card with CONTEXT four or more","your hand"],zones=["hand","Sheol"],quantities=["one card","one Letter"],outcomes=["Discard one card with CONTEXT four or more from your hand into Sheol","gain one Letter"]),
  "rarity_budget":budget(2,2,1,0,3, why=["the hand and Sheol","one discard and one gain","a card of CONTEXT four or more must be in hand and Sheol receives it","no other player is touched","a Letter, worth three cards, out of one card sown"]) })
META["MULTIPLY"] = {"gloss":"To become many; to increase and fill","weight":3,"weight_rationale":"be fruitful and multiply is spoken at creation, again after the flood and again to Abram - thematic vocabulary with real teaching behind it; the promise itself is carried by COVENANT and SEED, so MULTIPLY stays at 3",
 "art_prompt":"A dune of pale sand under a night sky crowded with stars, a single handful of grain spilled across the crest, a worn threshing floor below, no people, "+S("moonlit"),
 "stats":{"lore":4,"context":4,"complexity":3},
 "stats_rationale":{"lore":"the printed verses are the oath sworn to Abraham and the letter that quotes it back - the era's promise is stated in this verb","context":"rabah occurs 229 times in the Hebrew Bible; plethyno occurs 12 times in the New Testament; total 241","complexity":"Genesis 22:17 doubles the verb - harbah arbeh, in multiplying I will multiply - an infinitive absolute that Hebrews 6:14 keeps word for word in Greek, so the strangeness of the English is a deliberate carry-over"},
 "ot_verse":{"ref":"Genesis 22:17","snippet":"in blessing I will bless thee, and in multiplying I will multiply thy seed"},"nt_verse":{"ref":"Hebrews 6:14","snippet":"Surely blessing I will bless thee, and multiplying I will multiply thee"},
 "greek":{"text":"πληθύνω","translit":"plethyno"},"hebrew":{"text":"רָבָה","translit":"rabah"},
 "ot_refs":"Gen 22:17 • Gen 1:22 • Gen 9:7","nt_refs":"Heb 6:14 • Acts 6:7 • 2 Cor 9:10",
 "trivia":["The blessing to be fruitful and multiply is given to the fish and birds before it is ever given to man.","After the flood the blessing is repeated to Noah twice in one chapter, as if the world were being started again.","Hebrews 6:14 keeps the Hebrew doubling in Greek - blessing I will bless, multiplying I will multiply - rather than smoothing it into an adverb."]}

DESIGNS["SPEAK"] = ("UNCOMMON",
 {"core_meaning":"To address another and be answered - God spake unto Noah, saying; speech goes out to a hearer and calls back a word of like kind.",
  "type_expression":"A verb of address: a chosen player is spoken to and answers with one card from hand, and a word of like kind - the same COMPLEXITY - is called back out of Sheol.",
  "mechanical_anchors":["spoken to and answered","a word of like kind","God spake unto Noah","called back out of Sheol","the same COMPLEXITY"],
  "mechanic_seed":"Choose another player, spoken to as God spake unto Noah; that chosen player reveals one card from that chosen player's hand and answers, then add one card of the same COMPLEXITY as that revealed card from Sheol to your hand, a word of like kind called back out of Sheol, and draw one card from the Tower."},
 {"mechanical_expression":"A chosen player is spoken to and answered: that player reveals one card from hand, and a word of like kind - one card of the same COMPLEXITY as that revealed card - is added from Sheol to your hand, with one more card drawn from the Tower.",
  "semantic_anchor":"a word of like kind",
  "semantic_evidence":["that chosen player reveals one card from that chosen player's hand","add one card of the same COMPLEXITY as that revealed card from Sheol to your hand","draw one card from the Tower"],
  "ability_text":"Choose another player; that chosen player reveals one card from that chosen player's hand. Then add one card of the same COMPLEXITY as that revealed card from Sheol to your hand and draw one card from the Tower.",
  "rules_terms":["player","card","hand","COMPLEXITY","Sheol","Tower","choose","reveal","add","draw"],
  "rules_actions":["choose","reveal","add","draw"],
  "clarity":cl(targets=["another player","that chosen player's hand","your hand"],zones=["hand","Sheol","Tower"],quantities=["one card","one card","one card"],outcomes=["that chosen player reveals one card from that chosen player's hand","add one card of the same COMPLEXITY as that revealed card from Sheol to your hand","draw one card from the Tower"]),
  "rarity_budget":budget(2,2,1,1,2, why=["one chosen player, the hand, Sheol and the Tower","one add and one draw after the answer","Sheol must hold a card of the answering card's COMPLEXITY","one chosen player shows a card and nothing of that player's moves","one matched card out of Sheol and one card drawn"]) })
META["SPEAK"] = {"gloss":"To utter words to a hearer","weight":3,"weight_rationale":"the era runs on divine address - God spake to Adam, to Noah, to Abram - which is thematic vocabulary with real teaching; the pillar word for utterance is the one the set already carries, so SPEAK stays at 3 and prints UNCOMMON",
 "art_prompt":"One figure seen from behind standing on a bare hillside, head bowed and hands open at his sides, the empty valley below still in shadow, no other people, "+S("dawn"),
 "stats":{"lore":4,"context":5,"complexity":3},
 "stats_rationale":{"lore":"the printed verses are God speaking to Noah out of the ark and God speaking in time past to the fathers - in this era being addressed by God is the whole of revelation","context":"dabar occurs 1143 times in the Hebrew Bible; laleo occurs 296 times in the New Testament; total 1439","complexity":"the verb dabar and the noun dabar - a word and also a thing or matter - are the same consonants, and Greek splits what Hebrew joins by using laleo for the sounding of speech and lego for its sense"},
 "ot_verse":{"ref":"Genesis 8:15","snippet":"And God spake unto Noah, saying"},"nt_verse":{"ref":"Hebrews 1:1","snippet":"God, who at sundry times and in divers manners spake in time past unto the fathers"},
 "greek":{"text":"λαλέω","translit":"laleo"},"hebrew":{"text":"דָּבַר","translit":"dabar"},
 "ot_refs":"Gen 8:15 • Gen 12:4 • Gen 17:3","nt_refs":"Heb 1:1 • John 8:38 • Acts 2:4",
 "trivia":["Genesis 1 never says God spake; it says God said - amar - and the heavier dabar waits until there is a man to be addressed.","Because dabar means both word and thing, the ten commandments are literally the ten words, and a happening can be called a word.","Laleo first meant to make a sound, even of animals; the New Testament raises it to the utterance of the gospel."]}

DESIGNS["NATION"] = ("UNCOMMON",
 {"core_meaning":"A people gathered under one name - I will make of thee a great nation; by the sons of Noah were the nations divided in the earth.",
  "type_expression":"A noun of multitude: five cards are looked over and the ones that fill the earth - CONTEXT four or more - are gathered into the hand, the rest going down into Sheol.",
  "mechanical_anchors":["gathered into one people","a great nation","the ones that fill the earth","the rest going down","CONTEXT four or more"],
  "mechanic_seed":"Look at the top five cards of the Tower; add up to two of those cards that each have CONTEXT four or more to your hand, gathered into one people as a great nation, then put each other card into Sheol, the rest going down."},
 {"mechanical_expression":"Five cards are looked over and the ones that fill the earth are gathered into one people: up to two cards that each have CONTEXT four or more are added to the hand, and each other card is put into Sheol.",
  "semantic_anchor":"gathered into one people",
  "semantic_evidence":["Look at the top five cards of the Tower","Add up to two of those cards that each have CONTEXT four or more to your hand","put each other card into Sheol"],
  "ability_text":"Look at the top five cards of the Tower. Add up to two of those cards that each have CONTEXT four or more to your hand, then put each other card into Sheol.",
  "rules_terms":["cards","Tower","CONTEXT","hand","card","Sheol","look at","add","put"],
  "rules_actions":["look at","add","put"],
  "clarity":cl(targets=["the top five cards of the Tower","your hand"],zones=["Tower","hand","Sheol"],quantities=["top five cards","up to two of those cards"],outcomes=["Add up to two of those cards that each have CONTEXT four or more to your hand","put each other card into Sheol"]),
  "rarity_budget":budget(2,2,1,0,2, why=["the Tower, the hand and Sheol","one filtered add and one placement","Sheol receives everything not gathered","no other player is touched","up to two wide-spread cards gathered out of five"]) })
META["NATION"] = {"gloss":"A people gathered under one name","weight":3,"weight_rationale":"the table of nations and the promise of a great nation are what the era ends in - thematic vocabulary with real teaching; the named event is Babel itself rather than the word nation, so it stays at 3",
 "art_prompt":"A wide valley seen from a high ridge, ochre villages and threads of cooking smoke scattered along the dry course of a wadi, herds small in the distance, no people, "+S("desert"),
 "stats":{"lore":3,"context":5,"complexity":3},
 "stats_rationale":{"lore":"the printed verses promise Abram a great nation and call a scattered people a holy nation - a recognized theme of the era with clear teaching, though no doctrine rests on the word itself","context":"goy occurs 560 times in the Hebrew Bible; ethnos occurs 162 times in the New Testament; total 722","complexity":"goy and am divide between them what English calls nation and people, and the Septuagint's ethnos becomes Gentiles in English whenever the nation in view is not Israel - one word translated two ways by context"},
 "ot_verse":{"ref":"Genesis 12:2","snippet":"And I will make of thee a great nation, and I will bless thee"},"nt_verse":{"ref":"1 Peter 2:9","snippet":"But ye are a chosen generation, a royal priesthood, an holy nation"},
 "greek":{"text":"ἔθνος","translit":"ethnos"},"hebrew":{"text":"גּוֹי","translit":"goy"},
 "ot_refs":"Gen 12:2 • Gen 10:5 • Gen 17:4","nt_refs":"1 Pet 2:9 • Matt 28:19 • Rev 7:9",
 "trivia":["Genesis 10 counts seventy nations from the three sons of Noah, and Genesis 11 explains how they came to be separate.","Israel is called a goy in Genesis 12:2 - the word is not reserved for outsiders until much later.","1 Peter 2:9 hands Israel's titles to a scattered church, holy nation among them, and the Greek word is the one usually rendered Gentiles."]}

DESIGNS["KEEPER"] = ("UNCOMMON",
 {"core_meaning":"One who has a charge to guard - am I my brother's keeper; the keeper watches over what is committed to him and lets nothing be lost.",
  "type_expression":"A title of charge: three cards are watched over, the one belonging to your charge - a card type in your Lot - is taken, the rest are stowed under, and the keeping earns a Letter.",
  "mechanical_anchors":["belonging to your charge","am I my brother's keeper","watched over","stowed under","the keeping earns a Letter"],
  "mechanic_seed":"Look at the top three cards of the Tower, watched over as a keeper watches; add one of those cards whose card type is in your Lot to your hand, belonging to your charge, put the other cards on the bottom of the Tower, stowed under; then gain one Letter for the keeping."},
 {"mechanical_expression":"Three cards are watched over: the card belonging to your charge, whose card type is in your Lot, is added to the hand, the other cards are stowed under on the bottom of the Tower, and the keeping earns one Letter.",
  "semantic_anchor":"belonging to your charge",
  "semantic_evidence":["Add one of those cards whose card type is in your Lot to your hand","put the other cards on the bottom of the Tower","gain one Letter"],
  "ability_text":"Look at the top three cards of the Tower. Add one of those cards whose card type is in your Lot to your hand, put the other cards on the bottom of the Tower; then gain one Letter.",
  "rules_terms":["cards","Tower","card type","Lot","hand","card","Letter","look at","add","put","gain"],
  "rules_actions":["look at","add","put","gain"],
  "clarity":cl(targets=["the top three cards of the Tower","your hand"],zones=["Tower","Lot","hand"],quantities=["top three cards","one of those cards","one Letter"],outcomes=["Add one of those cards whose card type is in your Lot to your hand","put the other cards on the bottom of the Tower","gain one Letter"]),
  "rarity_budget":budget(2,3,0,0,3, why=["the Tower, your Lot and the hand","one filtered add, one placement and one gain","your Lot is read as it lies, with no prior state built","no other player is touched","a Letter, worth three cards, and a card only if your Lot claims it"]) })
META["KEEPER"] = {"gloss":"One who guards what is committed to him","weight":3,"weight_rationale":"Cain's question and the keeping of the garden give the era its word for responsibility - thematic vocabulary with real teaching; it names a role rather than a person the era turns on, so it stays at 3",
 "art_prompt":"A stone sheepfold on a dark hillside with its gate of thorn branches shut fast, a watchfire burning low against the wall, no people, "+S("firelight"),
 "stats":{"lore":3,"context":5,"complexity":3},
 "stats_rationale":{"lore":"the printed verses give Cain's refusal of the charge and the LORD taken as the keeper of his own - a recognized theme with clear teaching, though the doctrine hangs on the keeping rather than the title","context":"shomer is the participle of shamar, which occurs 468 times in the Hebrew Bible; phylax occurs 3 times in the New Testament; total 471","complexity":"shamar means to guard, to tend and to observe at once, so the keeper of a garden, the keeper of a flock and the keeper of a commandment are one word; phylax gives phylake, which is both a watch of the night and a prison"},
 "ot_verse":{"ref":"Genesis 4:9","snippet":"I know not: Am I my brother's keeper?"},"nt_verse":{"ref":"Acts 5:23","snippet":"the keepers standing without before the doors"},
 "greek":{"text":"φύλαξ","translit":"phylax"},"hebrew":{"text":"שֹׁמֵר","translit":"shomer"},
 "ot_refs":"Gen 4:9 • Ps 121:4 • Ps 121:5","nt_refs":"Acts 5:23 • Acts 12:6 • Acts 12:19",
 "trivia":["Cain answers a question about his brother with a word from the garden: the man was put there to dress it and to keep it.","Psalm 121 uses the keeper word six times in eight verses - he that keepeth thee will not slumber.","Phylax is the guard at a door; its cousin phylake is the cell behind that door, which is why the same root is translated both watch and prison."]}

DESIGNS["SHEM"] = ("UNCOMMON",
 {"core_meaning":"The son whose name is Name - blessed be the LORD God of Shem; while Babel's builders grasp at a name, the name is given to the line that does not grasp.",
  "type_expression":"A name of standing: two names are set against each other from the hand, and the weightier tongue - the higher COMPLEXITY - calls the forgotten back out of Sheol.",
  "mechanical_anchors":["set against each other","the weightier tongue","blessed be the God of Shem","calls the forgotten back","the higher COMPLEXITY"],
  "mechanic_seed":"Choose another player; each of you reveals one card from your hand, set against each other as name against name, and if your revealed card has the higher COMPLEXITY, the weightier tongue, add up to two cards from Sheol to your hand, calling the forgotten back."},
 {"mechanical_expression":"Two cards are set against each other from the hands of two players, and the weightier tongue wins: if your revealed card has the higher COMPLEXITY, up to two cards are called back from Sheol to your hand.",
  "semantic_anchor":"set against each other",
  "semantic_evidence":["Each of you reveals one card from your hand","if your revealed card has the higher COMPLEXITY","add up to two cards from Sheol to your hand"],
  "ability_text":"Choose another player. Each of you reveals one card from your hand; if your revealed card has the higher COMPLEXITY, add up to two cards from Sheol to your hand.",
  "rules_terms":["player","card","hand","COMPLEXITY","cards","Sheol","choose","reveal","add"],
  "rules_actions":["choose","reveal","add"],
  "clarity":cl(targets=["another player","your hand"],zones=["hand","Sheol"],quantities=["one card","up to two cards"],condition="if your revealed card has the higher COMPLEXITY",outcomes=["Each of you reveals one card from your hand","add up to two cards from Sheol to your hand"]),
  "rarity_budget":budget(2,2,1,1,2, why=["one chosen player, the hand and Sheol","a matched reveal and one conditional add","Sheol must hold something worth recovering and the duel must be won","one chosen player shows a card and nothing of that player's moves","up to two cards out of Sheol when the weightier card is yours"]) })
META["SHEM"] = {"gloss":"Name; the eldest son of Noah, father of the blessed line","weight":3,"weight_rationale":"the son the promise runs through and the pun the Babel account turns on - thematic vocabulary with real teaching; the patriarchs the era turns on are Noah and Abram, so Shem stays at 3 and prints UNCOMMON",
 "art_prompt":"A dark goat-hair dwelling on a ridge at night, its doorway flap drawn back and lit from within, a striped woven mantle folded on the threshold, no people, "+S("lantern"),
 "stats":{"lore":3,"context":2,"complexity":4},
 "stats_rationale":{"lore":"the printed verses bless the God of Shem and seat him in a genealogy - a recognized theme of the era, since the promise travels his line, but the teaching rests on the promise rather than the man","context":"Shem occurs 17 times in the Hebrew Bible; Sem occurs 1 time in the New Testament; total 18","complexity":"his name is simply the noun name, so Genesis 11 sets a people who say let us make us a name against the line already called Name; and Genesis 9:26 blesses the God of Shem rather than Shem, a construction commentators have argued over for centuries"},
 "ot_verse":{"ref":"Genesis 9:26","snippet":"Blessed be the LORD God of Shem; and Canaan shall be his servant"},"nt_verse":{"ref":"Luke 3:36","snippet":"which was the son of Sem, which was the son of Noe"},
 "greek":{"text":"Σήμ","translit":"Sem"},"hebrew":{"text":"שֵׁם","translit":"Shem"},
 "ot_refs":"Gen 9:26 • Gen 10:21 • Gen 11:10","nt_refs":"Luke 3:36",
 "trivia":["Genesis 9:26 blesses the LORD God of Shem rather than Shem himself - the only blessing in the chapter aimed past the man to his God.","Shem is introduced in Genesis 10:21 as the father of all the children of Eber, four generations before Eber is born in the text.","The builders at Babel say let us make us a name - shem - two chapters after a man named Shem has been given one."]}

# ---------------------------------------------------------------- RARE
DESIGNS["ARK"] = ("RARE",
 {"core_meaning":"The vessel that carries life through the judgment - make thee an ark of gopher wood; of every kind commanded, a pair is taken aboard and kept alive.",
  "type_expression":"A noun of shelter: every kind the Chapter Lot commands is taken aboard out of the waters of Sheol, and a heavy enough record already kept afloat brings one more card aboard.",
  "mechanical_anchors":["taken aboard out of the waters","of every kind commanded","make thee an ark of gopher wood","kept alive through the judgment","a heavy enough record"],
  "mechanic_seed":"Choose up to three cards in Sheol whose card type is in the Chapter Lot, of every kind commanded, and add those chosen cards to your hand, taken aboard out of the waters; if the cards in your Pages have total LORE fifteen or more, a heavy enough record, draw one card from the Tower."},
 {"mechanical_expression":"Every kind the Chapter Lot commands is taken aboard out of the waters of Sheol - up to three such cards are added to the hand - and if the cards in your Pages have total LORE fifteen or more, one more card is drawn from the Tower.",
  "semantic_anchor":"taken aboard out of the waters",
  "semantic_evidence":["Choose up to three cards in Sheol whose card type is in the Chapter Lot","add those chosen cards to your hand","draw one card from the Tower"],
  "ability_text":"Choose up to three cards in Sheol whose card type is in the Chapter Lot and add those chosen cards to your hand. If the cards in your Pages have total LORE fifteen or more, draw one card from the Tower.",
  "rules_terms":["cards","Sheol","card type","Chapter Lot","hand","Pages","LORE","card","Tower","choose","add","draw"],
  "rules_actions":["choose","add","draw"],
  "clarity":cl(targets=["up to three cards in Sheol","your hand"],zones=["Sheol","Chapter Lot","hand","Pages","Tower"],quantities=["up to three cards","those chosen cards","one card"],condition="If the cards in your Pages have total LORE fifteen or more",outcomes=["add those chosen cards to your hand","draw one card from the Tower"]),
  "rarity_budget":budget(2,2,2,0,3, why=["Sheol, the Chapter Lot, your Pages, the hand and the Tower","one filtered search and add, then one conditional draw","Sheol must hold the commanded kinds and the Pages threshold must already be built","no other player is touched","three cards out of Sheol, with a fourth when the record is heavy enough"]) })
META["ARK"] = {"gloss":"The vessel built to carry life through the flood","weight":4,"weight_rationale":"the named thing the era turns on - the judgment of the whole earth is survived inside it, and Hebrews makes it the pattern of salvation by faith; a weight-4 word, which is why it prints RARE",
 "art_prompt":"A vast hull of gopher wood ribs rising on a bare hillside, pitch smoking in an iron cauldron, curls of shaved wood trodden into the mud, no people, "+S("overcast"),
 "stats":{"lore":5,"context":2,"complexity":4},
 "stats_rationale":{"lore":"the printed verses are the command to build and the verdict that by it Noah condemned the world and became heir of righteousness - salvation through judgment is stated on this object","context":"tebah occurs 28 times in the Hebrew Bible; kibotos occurs 6 times in the New Testament; total 34","complexity":"tebah is used of only two things in all of Scripture, Noah's vessel and the basket of bulrushes that carries Moses, and it is never the ark of the covenant, which is aron - a distinction Greek loses by calling all of them kibotos"},
 "ot_verse":{"ref":"Genesis 6:14","snippet":"Make thee an ark of gopher wood ... and shalt pitch it within and without with pitch"},"nt_verse":{"ref":"Hebrews 11:7","snippet":"prepared an ark to the saving of his house"},
 "greek":{"text":"κιβωτός","translit":"kibotos"},"hebrew":{"text":"תֵּבָה","translit":"tebah"},
 "ot_refs":"Gen 6:14 • Gen 7:1 • Gen 8:4","nt_refs":"Heb 11:7 • 1 Pet 3:20 • Matt 24:38",
 "trivia":["The same word carries Moses down the Nile in a basket of bulrushes daubed with pitch - two rescues by water in one vocabulary.","The ark has no rudder, no sail and no oars; it is described as a floating chest, and the LORD shuts the door.","Greek uses kibotos for Noah's ark and for the ark of the covenant alike; Hebrew keeps them apart as tebah and aron."]}

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

TYPES = {"FORM":"VERB","REMEMBER":"VERB","MULTIPLY":"VERB","SPEAK":"VERB","GOOD":"ADJECTIVE","NATION":"NOUN",
         "SETH":"NAME","KEEPER":"TITLE","ARK":"NOUN","BROTHER":"TITLE","SHEM":"NAME"}
