"""SODOM and DESTROYER promoted to RARE under the word-weight rule, with RARE-strength abilities."""
def cl(**k):
    base={"trigger":"activation","timing":"instantaneous","targets":[],"zones":[],"quantities":[],"duration":"instantaneous","condition":"none","outcomes":[]}; base.update(k); return base
def budget(*v, why):
    return {k:{"rating":r,"rationale":w} for k,r,w in zip(("scope","complexity","setup","interaction","payoff"), v, why)}
DESIGNS = {
 "SODOM": ("RARE", "038-sodom", "NAME",
  {"core_meaning":"The city of the plain on which fire rained - five cards fall into Sheol, a few are led out, and one more goes under.",
   "type_expression":"A name of a judged place: the top five cards of the Tower rain into Sheol, up to three are led out into hand, and one card from hand is buried.",
   "mechanical_anchors":["fire rains into Sheol","led out of the city","up to three saved","one more goes under","the top five fall"],
   "mechanic_seed":"Put the top five cards of the Tower into Sheol as fire rains, then lead up to three of those cards out into the hand, and put one card from the hand on the bottom of the Tower."},
  {"mechanical_expression":"Judgment falls first - the top five cards of the Tower rain into Sheol - then a few are led out of the city: up to three of those cards come into hand, and one card from hand goes under to the bottom of the Tower.",
   "semantic_anchor":"led out of the city",
   "semantic_evidence":["Put the top five cards of the Tower into Sheol","add up to three of those cards to your hand","put one card from your hand on the bottom of the Tower"],
   "ability_text":"Put the top five cards of the Tower into Sheol. Then add up to three of those cards to your hand and put one card from your hand on the bottom of the Tower.",
   "rules_terms":["cards","card","Tower","Sheol","hand","put","add"],
   "rules_actions":["put","add","put"],
   "clarity":cl(targets=["the top five cards of the Tower","your hand"],zones=["Tower","Sheol","hand"],quantities=["top five cards","up to three of those cards","one card"],outcomes=["Put the top five cards of the Tower into Sheol","add up to three of those cards to your hand","put one card from your hand on the bottom of the Tower"]),
   "rarity_budget":budget(2,3,1,0,3, why=["the Tower, Sheol and the hand","a mill, a scaling add, and a placement","Sheol receives five cards first","no other player is touched","up to three chosen cards for one buried, against one discard paid"])}),
 "DESTROYER": ("RARE", "054-destroyer", "TITLE",
  {"core_meaning":"The agent of God's wrath who strikes one household at midnight and leaves it stripped, while the one who sent him takes the spoil.",
   "type_expression":"A title of office: the destroyer is sent against one chosen player, whose two cards fall into Sheol; the sender draws two and takes one from the slain in Sheol.",
   "mechanical_anchors":["strikes one household","two cards fall into Sheol","sent against another player","takes the spoil","one from the slain"],
   "mechanic_seed":"Send the destroyer against one chosen player: two cards from that hand fall into Sheol; then the sender draws two cards from the Tower and takes one from the slain in Sheol into hand."},
  {"mechanical_expression":"The destroyer is sent against another player and strikes one household - two of that chosen player's cards fall into Sheol - and the sender takes the spoil: two cards drawn from the Tower and one from the slain added from Sheol.",
   "semantic_anchor":"strikes one household",
   "semantic_evidence":["Choose another player","that chosen player puts two cards from that chosen player's hand into Sheol","add one card from Sheol to your hand"],
   "ability_text":"Choose another player; that chosen player puts two cards from that chosen player's hand into Sheol. Then draw two cards from the Tower and add one card from Sheol to your hand.",
   "rules_terms":["player","cards","card","hand","Sheol","Tower","choose","put","draw","add"],
   "rules_actions":["choose","put","draw","add"],
   "clarity":cl(targets=["another player","that chosen player","your hand"],zones=["hand","Sheol","Tower"],quantities=["two cards","two cards","one card"],outcomes=["puts two cards from that chosen player's hand into Sheol","draw two cards from the Tower","add one card from Sheol to your hand"]),
   "rarity_budget":budget(2,3,1,1,3, why=["another player and three zones","a forced two-card loss, a two-card draw, and a Sheol add","the chosen player must hold cards; Sheol must hold one","one chosen player loses two cards","three cards gained against one discard paid, with the opponent two poorer"])}),
}
