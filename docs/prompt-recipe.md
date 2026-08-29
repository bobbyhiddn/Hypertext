# Hypertext Card Prompt Recipe
Series: 2026 Q1

## Goal
Produce a single JSON object per card that an image model can use to render a consistent trading card.
The output image must contain ONLY the card, with no extra border, matting, or text outside the card border.

## Inputs per card (author-facing)
Each card must define:

Identity
- number: 001, 002, ...
- word: MAGI
- gloss: learned visitors from the East
- card_type: NOUN | VERB | ADJECTIVE | NAME | TITLE

Rarity
- rarity_text: COMMON | UNCOMMON | RARE | GLORIOUS
- rarity_icon: diamond shape, color varies by rarity
  - COMMON: white diamond
  - UNCOMMON: green diamond
  - RARE: gold diamond
  - GLORIOUS: orange diamond

Artwork
- art_prompt: one scene, no text in art

Stats (1 to 5)
- lore: meta-narrative alignment
- context: occurrence bucket (not exact count)
- complexity: grammar depth

Ability text
- one short ability line
- must match rarity design rules:
  - COMMON: simple ability
  - UNCOMMON: suit-based
  - RARE: references stats
  - GLORIOUS: unique, can reference other cards

Scripture
- ot_verse_ref + ot_verse_snippet (short)
- nt_verse_ref + nt_verse_snippet (short)

Languages
- greek + greek_translit
- hebrew + hebrew_translit
- ot_refs (references only)
- nt_refs (references only)

Lexical rule for every verse and reference: the OT verse and each ot_refs entry must contain the card's Hebrew lemma (an inflected form of the same lemma counts; a different word from the same root does not), and the NT verse and each nt_refs entry must contain the card's Greek lemma. Never cite a verse that merely alludes to the subject. If the word never occurs in the Greek New Testament, the Greek panel carries the New Testament's own name for the same referent (Shinar -> Babylon) and the NT citations contain that word.

Trivia bullets
- 3 to 5 bullets, short

Hidden metadata (not rendered)
- wild_id + wild_counts_as if TITLE
- letter if not TITLE
- internal_notes

## One lemma, one card

A word may not enter the set as a derivative of a word already in it - a
different tense, number, or part of speech of the same root (CHOOSE / CHOSEN,
GATHER / GATHERING) - unless it prints different lemmas, and two cards may
never share a printed Hebrew lemma or a printed Greek lemma. Each card is a
word study; two cards on one root dilute the set.

Enforced deterministically by `hypertext.cards.lemma_uniqueness`: same Hebrew
text (points stripped), same Greek text (accents stripped), same Hebrew root
(consonant skeleton of the transliteration), or same English stem. The plan
phase fails closed on a conflict, and `hypertext lemma-audit --series
series/2026-Q1` reports every conflicting pair in a series. Check candidate
lemmas offline before spending renders.

## Art subject, motifs and lighting (2026-08-29)

The illustration depicts **this card's own scene** - what the printed OT verse
describes, or the object, place, creature, weather or light the word names.

- **The tower is not the set's wallpaper.** At 76 cards, 14 prompts showed a
  tower or ziggurat and about five were tower words. The tower may appear only
  for the words in `art.tower_allowlist` (BUILD, BRICK, CITY, SHINAR, HIGH,
  ASCEND, SCATTER, CONFUSE); the plan phase rejects any other prompt naming it.
- **Motif caps** (`art.motif_caps`): tower 8, city 10, plain 10, tent 8,
  water 12 out of 90. `hypertext art-audit` prints the histogram.
- **Lighting palette.** A prompt ends with the fixed medium clause plus
  exactly one clause from `art.lighting_palette` (golden, dawn, noon, storm,
  lantern, firelight, underwater, overcast, desert, moonlit). **Golden is the
  default and is not rationed** - it is the set's signature, restored at the
  user's own request as the authority from the printed cards. Reach for
  another clause when the scene genuinely needs it (a night, a storm,
  firelight, underwater), not to spread the histogram. `art-audit` reports
  the spread; nothing fails on it. The monotony worth fixing is the subject.
- **Figures** are unchanged: no crowds; prefer no people; one figure seen from
  behind when a person is essential.

## Output rules (image model constraints)
- Render only the card. No extra border outside the card.
- No top microtext like "GAME: HYPERTEXT".
- Rarity must render as: [small icon] [RARITY_TEXT], exactly.
- Icon shapes must be exact, flat, and minimal. No gradients. No added symbols.
- Stat pips must be circles only.
- No text inside the artwork panel.
- Greek and Hebrew must be legible. Hebrew right-to-left.

## Production workflow
Daily
1) Create meta.yml for the next card.
2) Generate card.json from the template (manual or scripted).
3) Run validation against the schema.
4) Generate image from card.json prompt and save to outputs/.
5) Commit.

Quarterly
1) Freeze the series folder (2026-Q1).
2) Generate decklist.yml from the cards present.
3) Export print-ready PDF from the compiled images and print specs.

Set theme: each Hypertext set is one fallen kingdom, in historical order. The first set (2026-Q1, Babel) covers the antediluvian-to-Babel era - creation, Eden, the flood, the Table of Nations, Babel. Art draws from the whole era, not the tower by default. The next set is Egypt, so Egyptian subjects are reserved for it.

Art style: the illustration panel is a luminous, vibrant, full-color cinematic oil painting with impressionistic brushwork - deep shadowed backgrounds lit by one radiant golden light source, rich saturated blues and golds, ethereal atmosphere, a strong symbolic subject - in the manner of the printed Hypertext set (example cards 001-020); never sepia, monochrome, engraving, etching, woodcut, or line art. The parchment-and-navy frame is the only antique element. Every art_prompt ends with 'luminous cinematic oil painting with impressionistic brushwork, deep shadowed background, one radiant golden light source, rich saturated blues and golds'.

Style consistency: the standard art style is the default for every card in a base set. A card that comes out beautiful but in a different register (a cool teal seascape among warm golden chiaroscuro) is repainted to the standard. Alternate styles are reserved for expansions decided at the set level, where every face shares the alternate.
