# Ability grammar — the spec

**Status:** decided 2026-08-28. Machine form: `schema/ability_grammar.yml`.
Pricing and vocabulary live in `package/hypertext/cards/abilities.py`; the
rulings abilities depend on are in `docs/rules.md` § Abilities.

## 1. What an ability is

One core motion, addressed to the activating player, in imperative active
voice, using only the closed vocabulary. Optionally: a cost paid first, one
kicker, one condition, and a timing.

```
ABILITY := [COST] CORE [KICKER] [CONDITION] [TIMING]
```

Rarity is not chosen; it is *priced*. The estimator reads the printed copy
and rates scope, complexity, setup, interaction, and payoff; each rating must
sit inside the tier's range, and the total inside the tier's total.

| Tier | Cost | Scope | Complexity | Setup | Interaction | Payoff | Total | Cards' worth |
|---|---|---|---|---|---|---|---|---|
| COMMON | 0 | 1–2 | 1–2 | 0 | 0 | 1 | 3–5 | one, beaten modestly |
| UNCOMMON | 0 | 1–2 | 1–3 | 0–2 | 0–2 | 2–3 | 5–8 | two or more |
| RARE | 1 discard | 2–3 | 2–3 | 1–3 | 0–3 | 3 | 9–14 | three or more, net of cost; every player reached or a structure scaled |
| GLORIOUS | 2 discards | 2–3 | 2–3 | 1–3 | 0–3 | 4 | 9–16 | wild: five or more, every player's material moved, or a structure bent — a big cost in the copy may buy it |

Power ladder (2026-08-28): each tier's floor moved up one step — the old
GLORIOUS strength is RARE, the old RARE strength is UNCOMMON — and GLORIOUS
gained a fourth payoff step, the *wild* step, which only GLORIOUS may print.
The wild step is judged on gross gain (five or more cards' worth, every
player's material moved together with a three-card gain, or a structure
bent), so a big cost is what makes a wild effect fair, not what shrinks it.

## 2. Values

- A card is one. A Letter is **three**.
- **Costs count.** A discarded or buried hand card is one unit of cost; a
  Letter spent is three. Every three units take one step off the payoff
  rating, never below one. So *"Gain one Letter, then discard three cards"*
  prices as UNCOMMON; *"Discard two cards, then gain one Letter"* as RARE.
- **Costs are a lever.** "Spend two Letters", "Discard three cards", or
  "Discard one of your Pages" may open an ability and buy an action a tier
  larger than the printed cost alone allows. A discarded Page goes to Sheol
  and scores nothing.
- Exclusive branches (`…; otherwise, …`) never add: an ability that either
  adds or draws delivers only its better branch.
- Every ability must beat *"Draw one card from the Tower."* Information,
  peeking, or blind reordering alone is worth nothing.

## 2b. Word weight

Rarity is priced from the ability, but the *word* has a floor of its own.
Weight (1–5, stated with a rationale beside the stats) is how much a card of
the word means in the set's story: 4 is a named judgment, agent, place,
patriarch, or event the era turns on (SODOM, DESTROYER, EDEN, ABRAM); 5 is a
pillar (SPIRIT, COVENANT, NOAH). Weight 5 must print GLORIOUS and weight 4 at
least RARE; the plan phase fails closed otherwise, and
`hypertext weight-audit` reports the set against its budget of 22 heavy words
and 9 pillars. A slot's ability is then designed to the slot's tier.

## 3. Interaction by tier

- **COMMON** never touches another player.
- **UNCOMMON** may target one chosen player: make that player reveal a card,
  put a card into Sheol, or spend a Letter.
- **RARE** may do the same more heavily, or reach every player with
  information (*"Each player reveals one card …"*).
- **GLORIOUS** alone moves every player's material (*"Each player draws /
  discards …"*).

The estimator distinguishes *reveal-reach* (interaction 1) from
*material-reach* (interaction 3) when a clause says "each player".

## 4. Vocabulary

Actions: `draw add look at reveal put choose name gain spend shuffle discard
return exchange activate`. `record` and `redeem` are turn stages, not ability
actions.

Zones: the Tower (top / bottom), hand, Sheol, Page / Pages, Lot / Lots, the
Chapter Lot, Letters.

Lots are named with words we already have: **the Chapter Lot** (shared),
**your Lot**, **another player's Lot**, **that chosen player's Lot**. No new
term.

## 5. Rulings abilities rely on

- **Pages keep their value.** A Page scores its Chapter Value once created; an
  ability may return a card from a Page to its owner's hand and the Page still
  scores in full.
- **Activate.** *"Activate that chosen card"* resolves the card's ability at
  once as if it were the revealed card: no Letter access cost, its printed
  rarity cost paid from the activating player's hand, the card returns to
  Sheol afterwards, and it cannot activate another card.
- **Lots move unrecorded.** When an ability moves a Lot between players or
  returns one for a new one, the Lot arrives unrecorded for everyone this
  Chapter.

## 6. Productions

See `schema/ability_grammar.yml` for the full menu with example copy, gain
values, and the tiers each option may appear at. In summary:

| Slot | Options |
|---|---|
| COST | spend N Letters · discard N from hand into Sheol · bury one hand card · discard one of your Pages (5–7 units; the Page scores nothing) |
| CORE | draw N · add from top / bottom · look-and-take (1–4, top or bottom) · reveal-and-take · reveal-and-test · recover from Sheol (up to N, filtered or paid) · mill-and-take · gain a Letter · scale off a Page or Lot · return Sheol cards to the Tower · return a card from a Page · exchange with Sheol or a player · reset the Tower from Sheol · activate a COMMON in Sheol · move a Lot |
| INTERACT | a chosen player reveals / loses a card / spends a Letter · each player reveals · each player draws or discards |
| KICKER | reorder · rest to bottom / top / Sheol · bury the looked card · bury a hand card · shuffle · name a type · peek · reveal the next · draw one more |
| FILTER | a type · the named type · the same type as … · a stat floor · a type in a Lot |
| CONDITION | revealed card is a type · revealed type is in a Lot · no type in hand · at least N cards in Pages · otherwise · for each |
| TIMING | now · at the start of your next turn |

## 6b. Stats as a design surface (2026-08-29)

Every card prints LORE, CONTEXT and COMPLEXITY, and at 76 cards two abilities
read one. Six productions put the pips in play:

| Production | Copy | Tiers |
|---|---|---|
| `stat_floor` | "...that each have LORE three or more" | any |
| `stat_match` | "one card of the same LORE as that added card" | UNCOMMON+ |
| `stat_condition` | "If that revealed card has CONTEXT four or more, ...; otherwise, ..." | UNCOMMON+ |
| `stat_duel` | "each of you reveals one card from your hand. If your revealed card has the higher LORE, ..." | UNCOMMON+ |
| `stat_threshold` | "If the cards in your Pages have total LORE twelve or more, ..." | RARE+ |
| `stat_scale` | "draw one card from the Tower for each point of COMPLEXITY on that revealed card" | RARE+ |

`stat_scale` prices as three cards (the average pip), `stat_threshold` as
setup 2, `stat_duel` as interaction 1.

**Stat rhyme.** Read the stat the word is about: LORE for weight, glory,
depth, holiness, judgment and promise; CONTEXT for multitude, all, many,
gathering and filling; COMPLEXITY for tongue, name, confusion, foreignness
and division.

## 6c. Mechanic axes (2026-08-29)

An axis is a game surface an ability reads or moves. Per 90 cards:
stats 18, types 26, Letters 12, Lots 10, Pages 8, another player 16,
Sheol 24 (`mechanic_axis_targets` in `set-standards.yml`). A batch of ten
carries at least two stat readers, one Letter card and one Lot-or-Page card;
`scripts/pipeline/offline_check.py` fails closed and `hypertext axis-audit`
reports the set.

## 7. Uniqueness

- **Shape:** no two cards share a core motion plus qualifiers
  (`hypertext ability-audit --series`). COMMONs may rhyme; look count and
  destination make them distinct.
- **Lemma:** no derivatives of an existing word and no shared Hebrew or Greek
  lemma (`hypertext lemma-audit --series`).
- **Copy length:** COMMON 34 · UNCOMMON 40 · RARE 48 · GLORIOUS 56 words.

## 8. Coverage targets

Set targets are 36 / 32 / 13 / 9. Each batch of five spends at least two
cards on Letters, Lots, or Pages. The unused actions — `discard`, `return`,
`exchange`, `activate` — belong to RARE and GLORIOUS and should appear in the
next two batches.

## 9. Tooling

- `hypertext ability-audit --series … --show` — shape inventory and duplicates.
- `hypertext lemma-audit --series …` — lemma and word collisions.
- `hypertext grammar-check --series …` — classifies every ability into grammar
  productions and reports anything the grammar cannot name.
- The plan phase fails closed on a shape or lemma collision.
