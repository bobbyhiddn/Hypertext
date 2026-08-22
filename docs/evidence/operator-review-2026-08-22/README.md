# Gemini operator-review sample — 2026-08-22

This evidence set contains seven newly generated, full-resolution cards and two contact sheets. The standard sample covers NOUN/COMMON (`GRACE`), VERB/UNCOMMON (`FORGIVE`), ADJECTIVE/RARE (`ETERNAL`), and TITLE/UNCOMMON (`REDEEMER`). The Lot sample covers all supported forms: `SCROLL` (5-card), `ASSEMBLY` (6-card), and `REVELATION` (7-card).

## Validation

- `image-validation.json` verifies all 14 templates and all seven generated cards decode as PNG at exactly 1024×1536 pixels.
- Visual comparison against `contact-sheets/all-14-templates.png` confirms the generated cards retain the parchment, navy/gold framing, panel geometry, serif typography, icon language, and portrait layout of their references.
- Card titles, glosses, artwork subjects, stats, abilities, verse blocks, language blocks, and trivia agree with the saved prompts. Small header defects remain visible for operator review: the standard generator sometimes emits generic `Rarity` text and redundant type microtext (`NAME` or `TYPE`) instead of a clean rarity/type header.
- Lot rules agree with the saved prompts and project contract: 5-card = 8 board points / 2 letters, 6-card = 10 board points / 2 letters, 7-card = 14 board points / 3 letters; every card shows a +2 first-to-record wreath bonus. The displayed compositions contain exactly 5, 6, and 7 slots respectively, use unbracketed type names, and match each Lot's content.

## Operator attachments

- `contact-sheets/all-14-templates.png`
- `contact-sheets/fresh-7-card-sample.png`
- Individual full-resolution PNGs are under `cards/*/outputs/` and `lots/*/outputs/`.
