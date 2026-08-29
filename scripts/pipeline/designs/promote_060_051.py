"""EDEN and ABRAM promoted to RARE under the word-weight rule (user, 2026-08-28)."""
def cl(**k):
    base={"trigger":"activation","timing":"instantaneous","targets":[],"zones":[],"quantities":[],"duration":"instantaneous","condition":"none","outcomes":[]}; base.update(k); return base
def budget(*v, why):
    return {k:{"rating":r,"rationale":w} for k,r,w in zip(("scope","complexity","setup","interaction","payoff"), v, why)}
DESIGNS = {
 "EDEN": ("RARE", "060-eden", "NAME",
  {"core_meaning":"The garden planted at the beginning - abundance laid out, a portion taken, one tree lost, and the rest left beyond the gate.",
   "type_expression":"A name of a planted place: five cards are looked at from the top of the Tower, up to three are taken as the garden's fruit, one is lost into Sheol, and the remaining cards go beneath the Tower.",
   "mechanical_anchors":["the garden's fruit","one tree lost","beyond the gate","up to three taken","five laid out"],
   "mechanic_seed":"Look at five cards laid out from the top of the Tower; add up to three of those cards to the hand as the garden's fruit, put one of the other cards into Sheol as the one tree lost, and put each other card on the bottom of the Tower beyond the gate."},
  {"mechanical_expression":"Eden lays out five cards from the top of the Tower: up to three are added to hand - the garden's fruit - one of the other cards goes into Sheol, the one tree lost, and each other card goes on the bottom of the Tower.",
   "semantic_anchor":"the garden's fruit",
   "semantic_evidence":["Look at the top five cards of the Tower","Add up to three of those cards to your hand","put one of the other cards into Sheol"],
   "ability_text":"Look at the top five cards of the Tower. Add up to three of those cards to your hand, put one of the other cards into Sheol, and put each other card on the bottom of the Tower.",
   "rules_terms":["cards","Tower","hand","Sheol","look at","add","put"],
   "rules_actions":["look at","add","put","put"],
   "clarity":cl(targets=["the top five cards of the Tower","your hand"],zones=["Tower","hand","Sheol"],quantities=["top five cards","up to three of those cards","one of the other cards","each other card"],outcomes=["Add up to three of those cards to your hand","put one of the other cards into Sheol","put each other card on the bottom of the Tower"]),
   "rarity_budget":budget(2,3,1,0,3, why=["the Tower, the hand and Sheol","a five-card look, a scaling add, and two placements","Sheol receives one card","no other player is touched","up to three chosen cards against one discard paid"])}),
 "ABRAM": ("RARE", "051-abram", "NAME",
  {"core_meaning":"Called out of Ur to a land unseen, to become a blessing - a NAME that brings a Letter, and a blessing that reaches another.",
   "type_expression":"A name of a patriarch: the player draws, a NAME drawn brings a Letter of the covenant, and the blessing reaches another player who draws as well.",
   "mechanical_anchors":["called out to draw","a NAME brings a Letter","a blessing that reaches another","the covenant Letter","another player draws"],
   "mechanic_seed":"Draw one card from the Tower; if that drawn card is a NAME, gain one Letter of the covenant; then choose another player who draws one card from the Tower, the blessing that reaches another."},
  {"mechanical_expression":"Abram is called out to draw one card; a NAME brings a Letter - when that drawn card is a NAME the covenant Letter is gained - and the blessing reaches another player: that chosen player draws one card from the Tower.",
   "semantic_anchor":"a NAME brings a Letter",
   "semantic_evidence":["If that drawn card is a NAME, gain one Letter","that chosen player draws one card from the Tower"],
   "ability_text":"Draw one card from the Tower; if that drawn card is a NAME, gain one Letter. Then choose another player, and that chosen player draws one card from the Tower.",
   "rules_terms":["card","Tower","NAME","Letter","player","draw","gain","choose"],
   "rules_actions":["draw","gain","choose","draw"],
   "clarity":cl(targets=["that drawn card","another player","that chosen player"],zones=["Tower"],quantities=["one card","one Letter","one card"],condition="if that drawn card is a NAME",outcomes=["Draw one card from the Tower","gain one Letter","that chosen player draws one card from the Tower"]),
   "rarity_budget":budget(2,3,1,1,3, why=["the activating player, another player and the Tower","a draw, a conditional Letter, and a gift draw","the condition reads the drawn card's type","one chosen player draws a card","a card plus a Letter on a NAME, against one discard paid"])}),
}
