# Hypertext: Rules of Play

**Ruleset:** Babel Alpha (canonical model). This document is the authoritative
prose statement of the Hypertext game system. Where it disagrees with older
documentation, this document wins. Where it disagrees with the machine-readable
Lot rules (`templates/phases.yml`, `hypertext.lots.rules`) or the approved
template matrix, the numbers printed on approved templates win and this
document must be corrected to match them.

## Overview

Hypertext is a word-study card game for 2–8 players built on Biblical
vocabulary. Players write a **Chapter** together: they reveal Word Cards from
the Tower, activate abilities, and **Record** exact combinations of card types
that match the **Lots** in play. Recording the shared **Chapter Lot** creates a
**Page** — a scored, face-up set in front of you. Recording a **Portion Lot**
(your own or another player's) earns **Letters** instead, and scores nothing
directly.

The structure of a game is:

> **Game → Chapters → Chapter Lot + Portion Lots → Records → Pages / Sheol →
> Chapter scoring → full 90-card reset**

The Pages created during play collectively constitute the Chapter. When the
Chapter closes, every Page is scored, all 90 Word Cards are gathered and
reshuffled, and the next Chapter begins with a fresh Tower and a new Chapter
Lot. The player with the highest total after the final Chapter wins.

---

## Components

- **90 Word Cards** — the Tower (5 types × 4 rarities)
- **30 Lot Cards** — 5-, 6-, and 7-card recipes
- **Letter tokens**
- **2 Wreath tokens** — Record Wreath and Empty Wreath
- **Redeem markers** (one per player)
- **Score tracker**

---

## Card Anatomy

| Element | Description |
|---------|-------------|
| **Number** | Collector ID (#001–#090) |
| **Word** | The English word |
| **Gloss** | Short definition |
| **Type** | NOUN, VERB, ADJECTIVE, NAME, or TITLE |
| **Rarity** | COMMON, UNCOMMON, RARE, or GLORIOUS |
| **Printed cost** | Cards discarded from hand to activate (shown beside the rarity) |
| **Art** | Thematic illustration |
| **Stats** | LORE, CONTEXT, COMPLEXITY (1–5 each) |
| **Ability** | Effect when activated |
| **Verses** | OT and NT scripture references |
| **Hebrew/Aramaic · Greek** | Original-language forms |
| **Trivia** | Educational notes |

---

## Card Types

| Type | Icon | Role | Count |
|------|------|------|-------|
| **NOUN** | Closed book | Person, place, thing, or concept | 16 |
| **VERB** | Slanted pencil | Action or state | 20 |
| **ADJECTIVE** | Pencil with sparkle | Descriptive word | 20 |
| **NAME** | Feather quill | Proper noun (person or place) | 16 |
| **TITLE** | Ornate empty frame | Wild — may stand for NOUN or NAME when recording | 18 |

**Total: 90 cards.**

---

## Rarity and Printed Cost

| Rarity | Diamond | Printed cost (discard from hand) |
|--------|---------|----------------------------------|
| **COMMON** | White | 0 |
| **UNCOMMON** | Green | 0 |
| **RARE** | Gold | 1 |
| **GLORIOUS** | Orange | 2 |

The printed cost is paid every time the card is activated, regardless of how
the activation was accessed (see *Activation*).

---

## Lots

A **Lot** is a recipe: the exact type composition of a 5-, 6-, or 7-card set.
The 30 Lot Cards are universal across all Hypertext sets. Every Lot Card can
serve in either role:

| Role | Lifetime | Function |
|------|----------|----------|
| **Chapter Lot** | Current Chapter | One shared recipe everyone may Record against. Recording it creates a **Page** worth the Lot's Chapter Value. |
| **Portion Lot** | Current Chapter | A personal recipe assigned to one player. Anyone may Record against it for **Letters**; no Page is created. |

### Lot values by size

| Lot size | Chapter Value (as Chapter Lot) | Owner Letters (own Portion Lot) | Visitor Letters (another's Portion Lot) |
|----------|--------------------------------|------------------------------|--------------------------------------|
| 5-card | 8 points | 2 | 1 |
| 6-card | 10 points | 2 | 1 |
| 7-card | 14 points | 3 | 2 |

- **Chapter Value** — the points a Page is worth when the Chapter is scored. Printed on the Lot face as `CHAPTER VALUE: n POINTS`.
- **Owner Letters** — earned by Recording *your own* Portion Lot.
- **Visitor Letters** — earned by Recording *another player's* Portion Lot.

The Lot face prints both Letter values on one line as the visitor/owner
split: `PORTION VALUE: 1/2 LETTERS` on 5- and 6-card Lots and
`PORTION VALUE: 2/3 LETTERS` on 7-card Lots — read it as
*visitor Letters / owner Letters*. Canonical faces: `templates/lot/v002/`.

Because only Chapter Lot Records create Pages, and every player may Record the
Chapter Lot once per Chapter, the points available in a Chapter are bounded by
one Page per player plus Letters and Wreaths.

### The 30 Lots

**5-card** (14): Remnant (4 of one type + 1 any) ·
Pentateuch (NOUN + VERB + ADJ + NAME + TITLE) ·
Scroll (VERB ×2 + ADJ ×2 + TITLE) ·
Witness (NAME ×2 + VERB ×2 + ADJ) ·
Epistle (NAME + VERB ×2 + NOUN ×2) ·
Psalm (ADJ ×3 + VERB + NOUN) ·
Parable (NOUN ×3 + VERB + ADJ) ·
Oracle (VERB ×3 + NAME + ADJ) ·
Covenant (NAME ×2 + NOUN ×2 + TITLE) ·
Benediction (TITLE ×2 + ADJ + NOUN + NAME) ·
Altar (NOUN ×3 + VERB + TITLE) ·
Foundation (NAME ×3 + NOUN + VERB) ·
Proverb (ADJ ×2 + VERB + NOUN + TITLE) ·
Lament (ADJ ×3 + NOUN + NAME)

**6-card** (12): Congregation (4 of one type + 2 any) ·
Assembly (3 of one type + 3 of another type) ·
Trinity (NAME ×2 + NOUN ×2 + VERB ×2) ·
Tabernacle (NOUN ×3 + NAME ×2 + TITLE) ·
Chorus (VERB ×3 + ADJ ×2 + NOUN) ·
Sanctuary (NOUN ×4 + NAME + TITLE) ·
Hymnal (ADJ ×2 + VERB ×2 + NOUN ×2) ·
Gospel (NAME ×2 + VERB ×2 + NOUN + TITLE) ·
Jubilee (VERB ×3 + ADJ ×2 + NAME) ·
Wisdom (ADJ ×3 + NOUN ×2 + TITLE) ·
Prophecy (ADJ ×2 + NAME ×2 + VERB ×2) ·
Selah (5 of one type + 1 any)

**7-card** (4): Creation (all 5 types + a pair) ·
Revelation (NOUN + VERB + ADJ + NAME + TITLE ×3) ·
Exodus (VERB ×3 + NAME ×2 + NOUN ×2) ·
Apocalypse (4 of one type + 3 of another type)

Canonical compositions live in `templates/phases.yml` (typed grammar:
`fixed` recipes list exact types; `groups` recipes name counted groups —
*n of one type*, *n of another type*, *any*; Creation is *all 5 types +
a pair*). The machine evaluator is `hypertext.lots.patterns`.
---

## Game Length

| Mode | Chapters | Flavor |
|------|----------|--------|
| **Quick** | 3 | *"On the third day He rose"* |
| **Standard** | 6 | *"Two were proposed, that twelve be restored"* |
| **Epic** | 12 | *"Twelve apostles; twelve gates"* |

Standard (6 Chapters) is the recommended default. Quick (3 Chapters) is the
recommended starting point for large tables. Redeem is disabled in two-player
games. Six-to-eight-player play is supported but remains subject to Alpha
playtesting.

---

## Objects and Zones

| Object | Lifetime | Function |
|--------|----------|----------|
| **Word Cards** | Whole game | The 90-card corpus, reconstituted into the Tower each Chapter |
| **Tower** | Current Chapter | Face-down draw pile |
| **Hand** | Current Chapter | Private Word Cards held by a player |
| **Resolve** | One activation | Temporary area holding the activated card and the cards paid as its cost until the ability finishes |
| **Sheol** | Current Chapter | Shared face-up discard pile: activated cards, activation costs, cards Recorded to any Portion Lot, End discards, ability discards, and the seeded Chapter-start card |
| **Chapter Lot** | Current Chapter | Shared recipe available to every player; Recording it creates a Page |
| **Portion Lot** | Current Chapter | Personal recipe assigned to one player, visible to all; Recording it earns Letters |
| **Page** | Current Chapter | Scored face-up set created by Recording the Chapter Lot |
| **Used Chapters** | Whole game | Completed Chapter Lots; they do not repeat during the game |
| **Letters** | Current Chapter | Open resource tokens; spent on activations or retained for score |
| **Wreaths** | Current Chapter | Chapter bonus tokens (+2 points each) |
| **Redeem marker** | Current Chapter | Marks a player who owes a Redeem-debt discard |

### Visibility

| Location | Visibility |
|----------|------------|
| Hand | Hidden (yours only) |
| Tower | Hidden |
| Pages, Sheol, Resolve, Lots, Letters, Wreaths | Open |

---

## Chapter Setup

1. Gather all 90 Word Cards and shuffle them to form the Tower.
2. Move the top card of the Tower face-up to Sheol. This seeded card cannot be Redeemed.
3. Reveal one Chapter Lot from the Lot deck that has not been used this game.
4. Deal two Lot Cards face-down to each player as Portion Lot candidates.
5. Each player chooses one candidate as their Portion Lot, before receiving Word Cards.
6. Reveal the chosen Portion Lots face-up in front of their owners. Return the unchosen candidates to the Lot deck.
7. Deal seven Word Cards to each player.
8. Reset Letters, Wreaths, Record markers, Redeem markers, and temporary effects.
9. Establish the starting player. The starting player rotates clockwise after each Chapter.

---

## Turn Structure

Each turn has four stages, in order:

1. **Reveal**
2. **Activate**
3. **Record**
4. **End**

### 1. Reveal

Reveal the top card of the Tower, then choose one:

**Draw Activation** — activate the revealed card.
- Spend **0 Letters**.
- Pay its printed rarity cost from hand.
- Place the card and its payment in Resolve, resolve the ability, then move everything in Resolve to Sheol.
- The revealed card is *not* added to your hand, and no additional card is drawn.

**Pass** — decline the activation.
- Add the revealed card to your hand.
- Draw one additional card into your hand.
- Neither card receives a Draw Activation.

The choice is: *activate the revealed card, or gain two cards.*

### 2. Activate

After Reveal resolves, you may activate cards from your hand. Each **Hand
Activation** costs **1 Letter** plus the card's printed rarity cost. Hand
Activations are repeatable as long as you can pay.

Letters earned later this turn (during Record) cannot be spent until a future
turn.

#### Activation costs

| Access | Letter cost | Printed cost |
|--------|-------------|--------------|
| Draw Activation (revealed card) | 0 | As printed (0 / 0 / 1 / 2) |
| Hand Activation (card from hand) | 1 | As printed (0 / 0 / 1 / 2) |

A zero-Letter Draw Activation does not waive the printed cost.

#### Cost resolution

For every activation:

1. Declare the activation.
2. Pay the Letter access cost, if any.
3. Pay the printed discard cost from hand.
4. Move the activated card and the payment cards to Resolve.
5. Resolve the ability.
6. Move everything in Resolve to Sheol.

Cards in Resolve cannot be targeted by the ability currently resolving, so an
ability can never retrieve its own cost before that cost reaches Sheol.
Activated cards and their costs cannot be Redeemed.

### 3. Record

You may Record exact card combinations from your hand that match any active
Lot. Every player may Record each active Lot **once per Chapter**, and may
Record several different Lots in one Record stage.

| You Record… | Matching cards go to | You gain | Page created? |
|-------------|----------------------|----------|---------------|
| **The Chapter Lot** | Your Pages, face-up | A Page worth the Lot's Chapter Value at Chapter scoring | **Yes** |
| **Your own Portion Lot** | Sheol | Owner Letters | No |
| **Another player's Portion Lot** | Sheol | Visitor Letters | No |

Procedure:

1. Choose the Lot.
2. Reveal the required cards from your hand.
3. Declare any TITLE substitution.
4. Verify the recipe matches exactly.
5. Mark yourself as having Recorded that Lot this Chapter.
6. If you Recorded the Chapter Lot, place the cards face-up in your Pages. Otherwise move them to Sheol and take the Letters.

The first player to Record the Chapter Lot takes the **Record Wreath**.

A Page stays face-up in front of you for the rest of the Chapter. Abilities
that refer to cards "in your Pages" see only the Pages you have created this
Chapter.

#### TITLE wild rule

A TITLE card may stand for **TITLE, NOUN, or NAME**. It may not stand for VERB
or ADJECTIVE. At most **one** TITLE substitution is allowed per Record; a TITLE
occupying an explicit TITLE slot in the recipe is not a substitution. Declare
the substituted role when presenting the Record.

### 4. End

1. Discard one card from hand to Sheol, if able.
2. Open the Redeem window on that discard (see *Redeem*).
3. Resolve any Redeem.
4. Check your hand. If it is empty, the Chapter closes (see *Closing the Chapter*). Otherwise play passes clockwise.

Only the active player can close a Chapter, and only after their complete turn
has resolved.

---

## Redeem

When a player makes their normal End discard, other players may **Redeem** it
— take it into hand.

- Redeem is disabled in two-player games.
- Only the normal End discard can be Redeemed. Activated cards, activation costs, Recorded cards, ability discards, the seeded Chapter-start card, and Redeem-debt discards can never be Redeemed.
- Priority starts with the next player clockwise from the discarding player and proceeds clockwise. The first eligible player who accepts becomes the **redeemer**.
- Each player may Redeem once per Chapter.
- The redeemer takes a Redeem marker. At the start of their next turn, before Reveal, they discard one card to Sheol. That debt discard cannot be Redeemed.
- Redeem debt expires at Chapter reset.

---

## Closing the Chapter

When the active player's hand is empty at the end of their turn:

1. Award the **Empty Wreath** to that player.
2. **Grace period:** each other player, in clockwise order, receives one final Record stage. They may Record any active Lot they have not already Recorded this Chapter. There is no Reveal, no activation, no Redeem, and no End discard during Grace. Pages and Letters earned during Grace count for scoring.
3. A player who empties their hand during Grace receives no Empty Wreath, but suffers no hand penalty.
4. Proceed to Chapter Scoring.

### Wreaths

| Wreath | Awarded to | Value |
|--------|------------|-------|
| **Record Wreath** | First player to Record the Chapter Lot | +2 points |
| **Empty Wreath** | The player who closes the Chapter | +2 points |

A player may earn both in the same Chapter.

---

## Chapter Scoring

Each player's Chapter score is:

> **Chapter Value of each Page created this Chapter**
> **+ remaining Letters × 3**
> **+ Wreath points**
> **− 1 per card remaining in hand**

- Spent Letters score nothing.
- Records to Portion Lots do not score directly; their value is the Letters they earned.
- Negative Chapter scores are permitted.
- Score exactly once, then add the result to the running total before reset.

---

## Chapter Reset

After scoring:

1. Move the completed Chapter Lot to Used Chapters. It does not repeat this game.
2. Return all Portion Lots to the Lot deck.
3. Gather all 90 Word Cards from every hand, the Tower, Sheol, Resolve, and every player's Pages.
4. Confirm all 90 cards are present.
5. Shuffle them into a fresh Tower.
6. Clear all Pages.
7. Reset Letters, Wreaths, Record markers, and Redeem markers.
8. End all temporary effects.
9. Rotate the starting player clockwise.
10. Begin the next Chapter Setup: reveal the next unused Chapter Lot and deal new Portion Lot candidates.

Because Pages exist only within a Chapter, any Page-dependent ability
accumulates during the current Chapter only and resets automatically.

---

## Tower Exhaustion

When the Tower is empty and a draw is required:

1. Shuffle the eligible cards in Sheol into a new Tower.
2. Exclude cards in Resolve.
3. Exclude an End discard whose Redeem window is still open.
4. Continue drawing.

If fewer cards exist than required, draw as many as possible.

---

## Ability Resolution Principles

Card text may create explicit exceptions to these rules. Otherwise:

- Costs are paid before effects.
- "Cannot" overrides "can".
- Required targets must exist; resolve the legal portions of an ability in written order.
- **Draw** means move a card from the Tower to hand. Draws caused by abilities never create a Draw Activation.
- **Discard** means move a card to Sheol. Only the normal End discard opens a Redeem window.
- Cards in Resolve cannot be targeted by the ability currently resolving.
- Temporary effects end at their stated duration or at Chapter reset, whichever comes first.
- Abilities that refer to Pages see only Pages created this Chapter.

---

## Game End

The game ends after the number of Chapters for the chosen mode. The player with
the highest total score wins.

### The Matthias Rule (tiebreaker)

> *"And they cast lots, and the lot fell on Matthias."* — Acts 1:26

If players are tied for the highest score after the final Chapter:

1. Only the tied players play a tiebreaker Chapter.
2. Shuffle the 90 Word Cards, seed Sheol, and deal seven cards to each tied player.
3. Reveal a new unused Chapter Lot. No Portion Lots are dealt.
4. Play proceeds normally (Reveal, Activate, Record, End).
5. The first player to Record the Chapter Lot wins the game. Nothing else is scored.

---

## Quick Reference

### Turn

| Stage | Actions |
|-------|---------|
| **1. Reveal** | Reveal top card: **Draw-Activate** it (0 Letters + printed cost) *or* **Pass** (keep it and draw 1 more) |
| **2. Activate** | Hand Activations: 1 Letter + printed cost each, repeatable |
| **3. Record** | Chapter Lot → Page (Chapter Value points) · Own Portion Lot → Sheol, Owner Letters · Other's Portion Lot → Sheol, Visitor Letters |
| **4. End** | Discard 1 (Redeem window) · empty hand closes the Chapter |

### Values

| Item | Value |
|------|-------|
| Printed cost | COMMON 0 · UNCOMMON 0 · RARE 1 · GLORIOUS 2 |
| Hand Activation access | 1 Letter |
| Chapter Value (5 / 6 / 7-card Page) | 8 / 10 / 14 points |
| Owner Letters (5 / 6 / 7-card) | 2 / 2 / 3 |
| Visitor Letters (5 / 6 / 7-card) | 1 / 1 / 2 |
| Record Wreath · Empty Wreath | +2 · +2 |
| Retained Letter | 3 points |
| Card left in hand | −1 point |

### Alpha hypotheses

The Letter values and Chapter Values above are Babel Alpha hypotheses and are
instrumented during playtesting. Individual Lots may eventually justify ±1
Letter adjustments. The printed cost matrix and the 20-template Word Card
matrix are locked.

---

## Glossary

| Term | Definition |
|------|------------|
| **Chapter** | One complete round of play, from a fresh Tower to full reset; the Pages created during it constitute the Chapter |
| **Chapter Lot** | The shared Lot for the current Chapter; Recording it creates a Page |
| **Chapter Value** | The points a Page scores (8 / 10 / 14 by Lot size) |
| **Portion Lot** | The Lot that falls to one player for the current Chapter (their portion); Recording it earns Owner Letters (owner) or Visitor Letters (anyone else) and scores nothing directly |
| **Page** | A face-up set created by Recording the Chapter Lot; worth its Chapter Value at Chapter scoring; cleared at reset |
| **Lot** | A 5-, 6-, or 7-card recipe of card types |
| **Record** | Play an exact match for a Lot from your hand |
| **Tower** | The face-down draw pile — language dispersed from Babel |
| **Sheol** | The shared face-up discard pile — the grave |
| **Resolve** | Where an activated card and its cost sit while the ability resolves |
| **Used Chapters** | Chapter Lots already completed this game |
| **Letter** | Resource token; spend 1 to activate from hand, or keep for 3 points each |
| **Draw Activation** | Activating the card you just revealed for 0 Letters |
| **Hand Activation** | Activating a card from hand for 1 Letter |
| **Printed cost** | Cards discarded from hand to activate: 0 / 0 / 1 / 2 by rarity |
| **Wreath** | +2-point bonus token: Record Wreath (first to Record the Chapter Lot) or Empty Wreath (closing the Chapter) |
| **Redeem** | Take another player's End discard into hand; owe a discard before your next Reveal; once per Chapter; disabled with 2 players |
| **Grace** | The final Record stage each other player receives after the Chapter closes |
| **Matthias Rule** | Tiebreaker Chapter with no Portion Lots; first to Record the Chapter Lot wins |

---

*Hypertext — Word by word, line upon line.*
