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

Trivia bullets
- 3 to 5 bullets, short

Hidden metadata (not rendered)
- wild_id + wild_counts_as if TITLE
- quartet_id + letter if not TITLE
- internal_notes

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
