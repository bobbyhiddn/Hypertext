# Hypertext Towerfall — roadmap

**Where the project actually is, 2026-08-29.** Set one, *Babel Alpha*, is complete: 90 Word
Cards and 30 Lots, every face gated and signed, print files committed, one physical deck ordered
from The Game Crafter. Two playtested iterations are behind us and a third is coming. The public
write-up and the card gallery are live on GitHub Pages. Publication is targeted for **2027**,
which leaves the intervening quarters for playtesting rather than production.

The generation problem is solved. What is left is a **game design** problem, a **publishing**
problem, and a short list of debts the build left behind.

Status key: **now** = in flight or next up · **next** = wanted, not started · **later** = after
set one is signed off · **done** = kept for the record.

---

## Now

### 1. Playtest three, and the rules that come out of it
**now** · owner: table, not pipeline

The printed deck exists to be played with. Two iterations have already moved the rules; the third
is the one that should either confirm the current economy or name the thing that is still wrong.

- [ ] Run playtest three with the printed deck, 3–4 players, full game rather than a single Chapter
- [ ] Record, per session: game length, scores, which abilities were never played, which Lots were
      never filled, and every rules question that had to be adjudicated at the table
- [ ] Fold the answers into `docs/rules.md` — every adjudication is either a rules bug or a
      wording bug, and both belong in the document before they are forgotten
- [ ] Re-check the **draw-one baseline**: any ability nobody spent is a card that lost to drawing

**Done when** a session runs start to finish with no adjudication that is not already in the rules.

### 2. Deterministic Lot type icons, and a gate that checks them
**now** · raised 2026-08-29 when REVELATION shipped with mismatched TITLE icons

Lot faces are painted from **prose** in `package/hypertext/lots/renderer.py` (`TYPE_ICONS`) — TITLE
is `"framed diamond/portrait icon"`. Nothing pins a glyph and nothing checks the result, so the
model free-styles per card. Word Cards solved this class of problem by stamping pips, the type
pill, number and footer after generation; Lot icons never got the same treatment.

Symptoms in the shipped set:

- **#28 REVELATION** printed three TITLE slots with two different glyphs, one filled and two
  outlined. Visible on the card.
- **#27 CREATION** carried the same filled glyph; it read as acceptable only because it has one
  TITLE with nothing beside it to clash with.
- Measured fill ratio across the set's 13 TITLE icons: eleven at 0.09–0.15, those two at 0.31–0.32.
- The prompt asks for NAME as a `"person silhouette"`, but every rendered Lot shows a **feather**.
  The model has been silently substituting the Word Card glyph, so the prose has been wrong all along.
- The vision gate checks slot count, plus count, exact strings, forbidden tokens and empty slots —
  but **not icon identity**, which is why this shipped.

- [ ] Extract five canonical glyphs (NOUN, VERB, ADJECTIVE, NAME, TITLE) as assets; a clean donor
      set exists on `02-pentateuch`
- [ ] Stamp them into the slot positions after generation the way `cards/fixed_elements.py` does,
      and remove icons from the generation prompt so the model stops painting them
- [ ] Gate a Lot face whose icons do not match the canonical glyphs
- [ ] Fix the `TYPE_ICONS` prose so the description matches what is actually drawn
- [ ] Re-stamp #27 and #28 and regenerate `series/2026-Q1/tgc_prep/lots/`

Both cards were repaired by hand on 2026-08-29 using correct cards as style references, so this is
now about **preventing the next one**, not fixing these two. Note that pixel surgery was tried and
reverted: the filled glyph's anti-aliased edge and shadow survive an ink-only erase, and a flat
patch does not match the parchment gradient.

### 3. Name the series something true
**now** · blocking nothing, embarrassing everything

The set lives at `series/2026-Q1`. It was not built in Q1, and it publishes in 2027. The id is
threaded through paths, the census, the gallery, the print files and the workflows, so this is a
rename with a migration, not a string edit.

- [ ] Decide the scheme: `babel-alpha` (name), `set-01` (ordinal), or a real date
- [ ] Write the migration — directory, `cards_index.yml`, `stats.yml`, workflow env, gallery links,
      `tgc_prep` paths — and keep a redirect for the published gallery URL
- [ ] Do it **before** the commercial print, not after

**Done when** no path in the repository claims a quarter the set was not made in.

### 4. Rotate the Gemini key
**now** · standing rule, generation has concluded

- [ ] Rotate `GEMINI_API_KEY` in `.env` and the `GEMINI_TEXT_API_KEY` repository secret
- [ ] Re-run `offline_check.py` and one render to confirm the new key works

---

## Next

### 5. A printed rulebook
**next**

`docs/rules.md` is a reference, not a rulebook. A boxed game needs something a table can read cold:
a first page that gets four people playing inside five minutes, then the reference behind it.

- [ ] Quick-start page: setup, a turn, how scoring works, when the game ends
- [ ] Worked example of a single Chapter with real cards
- [ ] Reference section: the wild TITLE rule, Pages, Letters, Sheol, the Record
- [ ] Lay it out to a print size that fits the box

### 6. Set two — the Egypt era
**next** · the foreshadow is already printed

Set one is antediluvian-to-Babel. Set two is Egypt. COVENANT already carries a foreshadow mechanic
pointing at it, so the promise is in players' hands.

- [ ] Word list, weighted the way set one was, with the **one-lemma rule enforced across sets** —
      no set-two word may share a lemma with a set-one card
- [ ] Decide what set two adds mechanically; a second set that plays identically is a reskin
- [ ] Re-target the mechanic axes for the new list rather than copying set one's
- [ ] Confirm two sets shuffle together cleanly for 7+ players, which the rules already promise

### 7. Close the loop on print
**next**

- [ ] Proof the delivered deck against the source faces — colour, bleed, the sigil's legibility at
      print size, and whether the stat pips survive the cut
- [ ] Write down what the print actually cost, per deck, at each quantity
- [ ] Decide the fulfilment path before the rulebook is laid out; it constrains the box

### 8. Pipeline debts
**next** · small, each worth doing before the next set

- [ ] `offline_check.py` takes a designs-module path; give it a `--series` mode so a whole set can
      be re-checked without writing a module
- [ ] The vision gate reads the ability text but not the transliteration line — SCATTER shipped
      with literal asterisks around a word and nothing caught it
- [ ] Lot faces have no equivalent of `contact_sheet.py`; building one would have caught #27 and
      #28 before the printer did
- [ ] The `2026-Q1-dev` scratch series is undocumented — say what it is for or delete it

---

## Later

### 9. Tabletop Simulator
**later** · `docs/How-To-TTS.md` exists; the export does not

Digital play is how a small game gets tested by people who do not live near you. Worth doing once
the rules stop moving.

### 10. What the pipeline is, separately from the game
**later**

The generation system is arguably more interesting to other developers than the card game is, and
it is now licensed for them to use. If that draws interest, the work is extracting it from this
repository's assumptions — a set standard, a designs module, a template package — so someone can
point it at their own subject.

---

## Done

- **Set one generated, gated and signed** — 90 Word Cards, 30 Lots, census 36/31/14/9, zero lemma
  conflicts, zero shared ability shapes, zero unclassified abilities
- **The gate suite** — stat pips, rarity chip, cost glyphs, placeholder leaks, exact ability text,
  three-vote style match, and set-wide audits for lemma, shape, weight, axes and art motifs
- **Deterministic fixed elements** — pips, type pill, number and footer stamped by code rather than
  asked for in a prompt
- **Templates and exemplars** — 20 card templates (5 types × 4 rarities), 3 Lot templates, and a
  reference pack restricted to a card's own type and rarity
- **Cryptographic watermark** — HMAC-SHA256 sigil burned into every face, failing closed without
  `HYPERTEXT_SIGNING_KEY`
- **Print preparation** — 122 files at 825 × 1125, frame-fit rather than stretched, committed with
  the set at `series/<id>/tgc_prep/`
- **The public site** — write-up and card gallery on GitHub Pages, built by `deploy-gallery.yml`
- **Licensing** — PolyForm Small Business for the software, CC BY-NC-SA 4.0 for the cards and art
- **Repository hardening** — Dependabot alerts and updates, secret scanning with push protection,
  actions restricted to GitHub-owned and verified, read-only default workflow token, and a ruleset
  blocking force-push and deletion on `main`
- **Model drift fixed** — `review.py` had fallen back to `gemini-2.0-flash` and Lot grading was
  pinned to `gemini-3-pro-preview`; both ids are gone from the API. Model choice now comes from
  `gemini.config` and a test fails on any id that is not the configured pair
