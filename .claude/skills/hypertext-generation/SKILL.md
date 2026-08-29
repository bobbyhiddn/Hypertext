---
name: hypertext-generation
description: Use when designing, generating, self-healing, auditing, or closing out a batch of Hypertext Babel Alpha Word cards - the designs-module -> driver daemon -> batch_run -> selfheal -> audits -> tracker/ledger/commit workflow. Also for redesigning or promoting an existing card, or regenerating legacy slots under the current contract.
---

# Hypertext generation (batch workflow)

The single-card module phases (`--phase plan|imagegen|revise|rebuild|grade`) are documented in the root
[SKILL.md](../../../SKILL.md). This skill is the batch workflow built on top of them: design offline,
answer the plan prompts from a designs module, render in a self-heal loop, audit, close out.

## Environment

- The repo venv is `.venv` (`python3 -m venv .venv && .venv/bin/pip install -e 'package[test]'`). Every script reads
  `HYPERTEXT_PY` (that python) and `HYPERTEXT_HX` (that venv's `hypertext` CLI). **Export both** - the
  scripts default to `python3` / `hypertext` on PATH, and a missing `hypertext` makes every self-heal
  attempt print `pip fail` (the gate command fails, not the pips) while burning a render per attempt.
- `GEMINI_API_KEY` lives in `.env` (gitignored); the scripts load it with `set -a; . ./.env; set +a`.
  Never echo it, never commit it, never pass it as an argument. Rotate the key when generation concludes.
- Models: images on `gemini-3.1-flash-image`, text/review on `gemini-3.7-flash`
  ([package/hypertext/gemini/config.py](../../../package/hypertext/gemini/config.py)).
- Scratch: a per-session directory (`$S`); keep `designs.py`, `spool/`, `batch.log`, `daemon.log`,
  `timing.txt` under `$S/batchN/`.

## 1. Read the set before designing

```bash
V=$HYPERTEXT_PY
$V -m hypertext.cli weight-audit  --series series/2026-Q1   # heavy-word budget 22/90, pillars 9
$V -m hypertext.cli lemma-audit   --series series/2026-Q1   # one-lemma rule
$V -m hypertext.cli ability-audit --series series/2026-Q1   # shape uniqueness (legacy shares are known)
$V -m hypertext.cli grammar-check --series series/2026-Q1   # cores used/unused per tier
python3 -c "import json;[print(c) for c in json.load(open('schema/babel_template_matrix.json'))['valid_combinations']]"
```

Targets per type x rarity: [series/2026-Q1/set-standards.yml](../../../series/2026-Q1/set-standards.yml)
(36/31/14/9 overall; `recount_census.py --dry-run` prints open slots). Open slots = target minus census. The canonical card list for the census test is
[series/2026-Q1/cards_index.yml](../../../series/2026-Q1/cards_index.yml) - append every new word.
Era: antediluvian to Babel (through Abram/Sodom); Egypt is set 2.

## 2. Design rules (all deterministic - the plan phase hard-fails on them)

- **Grammar** `ABILITY := [COST] CORE [KICKER] [CONDITION] [TIMING]` -
  [schema/ability_grammar.yml](../../../schema/ability_grammar.yml), [docs/ability-grammar.md](../../../docs/ability-grammar.md).
  Vocabulary is closed: actions draw/add/look at/reveal/put/choose/name/gain/spend/shuffle/discard/return/
  exchange/activate; zones Tower/hand/Sheol/Page(s)/Lot(s)/Chapter Lot/Letters. No invented keywords.
- **Power ladder** (`RARITY_BUDGETS` in [abilities.py](../../../package/hypertext/cards/abilities.py)):
  COMMON payoff 1, total 3-5, no cost beyond burying a hand card, no condition/interaction/Sheol/Pages/Letters;
  UNCOMMON payoff 2-3, total 5-8, may touch one chosen player; RARE payoff 3, total 9-14, may reach every
  player with information or scale a Lot/Page; GLORIOUS payoff 4, total 9-16, moves everyone's material or
  bends a structure. Every ability beats "Draw one card from the Tower."; costs subtract (card 1, Letter 3,
  Page 5+; one payoff step per 3 units). Declared ratings must equal `_estimate_printed_ratings`.
- **Render word caps** COMMON 34 / UNCOMMON 40 / RARE 48 / GLORIOUS 56; at most two sentences.
- **Word weight** 1-5 with a rationale; 5 -> GLORIOUS, 4 -> at least RARE. Budget 22 heavy words, 9 pillars.
- **One-lemma rule**: no shared Hebrew/Greek lemma, Hebrew root, or English stem with an existing card
  (NAME homographs exempt). **Shape uniqueness**: `ability_shape` signature must be new. Look count and
  rest-destination distinguish COMMON rhymes; a look or take FROM the bottom is a different play from a
  placement onto it; and your Lot / the Chapter Lot / another player's Lot are three different filters.
- **Verse lexical rule**: the printed OT/NT verse and ref strips contain the card's own lemma; names absent
  from the NT (Ham, Japheth, Nimrod...) cannot be cards until a NT verse exists.
- **Stats**: LORE and COMPLEXITY are judgments with a reason; CONTEXT is the bucket of Hebrew+Greek
  occurrence totals (<=10:1, 11-40:2, 41-120:3, 121-400:4, >400:5) and the rationale must read
  "X occurs N times ...; Y occurs M times ...; total T". COMMON/UNCOMMON may not carry three stats of 4+,
  a row totalling 13+ needs weight 4+, and a numeral or function word caps CONTEXT at 3. LORE and
  COMPLEXITY are scored on the era's use and THIS card's printed verses, never a doctrinal use elsewhere.
- **Stat gates must gate**: a per-card floor is "four or more" (LORE 46% of the set, CONTEXT 49%,
  COMPLEXITY 31%); "three or more" passes ~89% and gates nothing. A Page stat total is read on ONE Page at
  "twenty-two or more" (a 5-card Page averages 18, a 7-card 25).
- **Rulings** (docs/rules.md "Abilities"): "your Lot" / "another player's Lot" / "the Chapter Lot";
  **Pages are sealed** - a card never leaves a Page, so a Page may only be READ or DISCARDED WHOLE as a
  cost; "activate that chosen card"; interaction by tier; a Letter is worth three cards.
- **Validator quirks**: never "the other" unless followed by "card(s)" ("put each other revealed card...");
  never "it/them/this way/if not"; `discard` states hand -> Sheol; `draw` names the Tower; `return` names both
  zones; `shuffle the cards in the Tower`; `name` says "card type"; separate "Choose another player." from
  the action sentence; the ability copy must contain at least two non-rules words from the seed
  (see `_GENERIC_SEMANTIC_WORDS`) - bottom/top/look/those/revealed/whose count, hand/card/draw do not.
- **Art**: the illustration is THIS card's own verse scene. The tower is the set's namesake and is
  **rationed, not banned** - allowlist words always, any other word while the set is under
  `art.motif_caps.tower` (12 of 90). Lighting is **guidance**: the golden clause is the set's signature and
  the default; reach for another palette clause only when the scene needs it, never to spread a histogram.
  No crowds, no figure facing the viewer, "no people" unless one figure seen from behind. Stat pips, type
  pill, number and footer are stamped deterministically - the image prompt zeroes them; the rarity chip and
  cost glyphs are painted by the model and verified by gates.
- **Mechanic axes**: per 90 cards stats 18, types 26, Letters 12, Lots 10, Pages 8, opponent 16, Sheol 24
  (`set-standards.yml`); a batch of ten carries at least 2 stat readers, 1 Letter card and 1 Lot-or-Page
  card - `offline_check.py` fails closed. Prefer cores unused at that tier (`grammar-check` lists them).

## 3. Designs module

Copy the shape of [scripts/pipeline/designs/batch7_062_066.py](../../../scripts/pipeline/designs/batch7_062_066.py):
`DESIGNS[WORD] = (RARITY, seed, candidate)`, `META[WORD]` (gloss, weight, weight_rationale, art_prompt,
stats, stats_rationale, ot_verse/nt_verse, greek/hebrew, ot_refs/nt_refs, trivia x3), `critic_json(word)`,
plus `TYPES = {WORD: TYPE}`. The daemon answers the seed/candidate/critic/metadata prompts from it verbatim.

Pre-flight offline before any render - fix until it prints `0 finding(s)`:

```bash
$HYPERTEXT_PY scripts/pipeline/offline_check.py $S/batch8/designs.py
```

## 4. Launch

```bash
export HYPERTEXT_PY=$S/testenv/bin/python HYPERTEXT_HX=$S/testenv/bin/hypertext HYPERTEXT_TEXT_DRIVER_DIR=$S/batch8/spool
mkdir -p $S/batch8/spool
setsid nohup $HYPERTEXT_PY scripts/pipeline/driver_daemon.py $S/batch8/designs.py $S/batch8/spool > $S/batch8/daemon.log 2>&1 &
echo "START $(date +%H:%M:%S)" > $S/batch8/timing.txt
setsid nohup bash -c "scripts/pipeline/batch_run.sh WORD:TYPE:RARITY ... 2>&1 | while IFS= read -r l; do echo \"\$(date +%H:%M:%S) \$l\"; done; echo \"END \$(date +%H:%M:%S)\" >> $S/batch8/timing.txt" > $S/batch8/batch.log 2>&1 &
```

`batch_run.sh` per word: append to `deck/queue.yml` -> `--phase plan --auto` (daemon answers; word weight,
lemma and shape checks hard-fail here) -> validate -> census bump in `schema/babel_template_matrix.json` ->
`REGEN=1 selfheal.sh SLUG`. `selfheal.sh`: rebuild -> fixed elements -> visual gate -> 3-vote grade ->
single-defect image-only fix-mode (score >= 90, or the figure rule at any score), up to six attempts;
every attempt's verdict is archived under `outputs/grades/`. Expect ~65 s per card when it passes first.

Wait with a background `until grep -q END timing.txt` loop, not polling. Read `batch.log` for
`planned`, `aN: pips ok, Final Score`, `FULL PASS`, `single defect`. Interpret:

- `PLAN FAILED` -> read `/tmp/plan-WORD.log`: a rule the offline check missed; fix the module, restart
  the daemon (it imports the module once), re-run that word.
- `aN: pip fail` on every attempt within ~20 s -> `HYPERTEXT_HX` unset or wrong (gate command failing).
  A real pip defect shows in `outputs/visual-gate.json` `defects`.
- Repeated < 90 scores -> read `outputs/grades/aN.txt`; text garbles mean the copy is over the cap;
  crowd/figure means the art prompt needs "no people".
- To resume one card after a stop: `REGEN=1 scripts/pipeline/selfheal.sh SLUG` (the queue entry, card dir
  and census bump already exist - do not re-run `batch_run.sh` for it).
- Repaint only the art: `scripts/pipeline/repaint.sh SLUG`.

## 5. Close out

1. Eyeball every face: `$HYPERTEXT_PY scripts/pipeline/contact_sheet.py $S/batch8/sheet.jpg 067-walk ...`
   then Read the jpg. Check pips match stats, the chip word, cost glyphs on RARE+, lemmas, art subject.
2. Re-run the four audits from step 1; `cards_index.yml` gets the new words; `pytest` census test passes.
3. Archive the module: `cp $S/batch8/designs.py scripts/pipeline/designs/batch8_067_076.py`.
4. Tracker state [series/2026-Q1/tracker-state.json](../../../series/2026-Q1/tracker-state.json):
   `pilot["<n>"] = {"status": "pass", "note": "WORD TYPE/RARITY. <mechanic>. lemma / lemma (refs). Stats a/b/c. Weight w. attempts, score."}`
   and a `log` entry (`when` absolute date, `what` with launch/finish times, renders per card, self-heals).
   Rebuild the tracker page: `$HYPERTEXT_PY scripts/babel/build_set_tracker.py` -> `$S/babel-alpha-set.html`.
5. Ledger: add a `<li><span class="mono">DATE</span>...</li>` after `<ul class="log">` in `$S/lot-ledger.html`.
6. Artifacts (set tracker `09abca71-a5f9-4684-af27-474668529a02`, Lot ledger `22dacdf4-8971-4823-8197-584891557552`):
   another live session may republish them - `action: "read"` first, merge, then publish with `url`, no favicon.
7. Commit everything the batch touched (cards/, queue.yml, matrix, stats.yml, cards_index.yml, tracker-state,
   designs module) with the batch summary and timing; push to `github main` (PNGs go through LFS).
8. Print set, once the whole set passes: `$HYPERTEXT_PY -m hypertext.tgc prep --cards-dir series/2026-Q1/cards`
   writes `series/2026-Q1/tgc_prep/` (committed with the set) - both decks in 25-card
   upload batches at 825x1125, plus `templates/card_back.png` and `templates/lots/Lot_Back.png`.
   Faces are frame-fit, never stretched or cropped. Regenerate whenever a card changes.
9. Report: launch/finish times, seconds per card, renders per card, self-heals, audit lines, open slots.

## Redesign / promotion of an existing card

Write a designs module for the word (same format), stop the queue step: run the plan phase directly
against the existing card directory or follow the `promote_*.py` modules; update `cards_index.yml` and
the matrix counts by hand when rarity changes; then `REGEN=1 selfheal.sh SLUG`.
