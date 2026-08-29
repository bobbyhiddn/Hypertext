# Hypertext

A daily word-study trading card project featuring Biblical Greek and Hebrew terms.

## Overview

Hypertext produces collectible trading cards that explore words from Scripture. Each card includes:
- Original language forms (Greek and Hebrew)
- Scripture references from both Old and New Testaments
- AI-generated artwork (Gemini 2.0 Flash)
- Cryptographic watermark (sigil) for authenticity
- Trivia and linguistic notes

## Repository Structure

```
hypertext/
├── series/               # Card series
│   └── 2026-Q1/          # Series root ("the set")
│       ├── cards/        # Source of truth: one folder per card
│       ├── lots/         # Lot faces (flat PNG package) + manifest
│       ├── deck/         # queue.yml
│       ├── tgc_prep/     # PRINT-READY OUTPUT, committed with the set
│       ├── tracker/      # Generated set tracker page
│       ├── set-standards.yml   # Grid targets, mechanic axes, art rules
│       ├── cards_index.yml     # Canonical card list
│       └── tracker-state.json  # Per-slot status and the build log
├── package/hypertext/    # The library (cards, gemini, lots, tgc, gallery, cli)
├── scripts/pipeline/     # batch_run, selfheal, replan, offline_check, designs/
├── templates/            # Card + lot templates, card_back.png, lots/Lot_Back.png
├── schema/               # Card schema, ability grammar, template matrix
├── docs/                 # rules.md, ability-grammar.md, prompt-recipe.md, How-To-TGC.md
└── tools/                # verify_template_package.py
```

### Print output lives with the set

`series/<id>/tgc_prep/` is committed, so the exact files that were sent to the
printer are recoverable for any past state of the set:

```
tgc_prep/
├── cards/batch_01..04/   # 90 faces, 25 per upload batch
├── cards/back/           # navy Word back
├── lots/batch_01..02/    # 30 Lot faces
└── lots/back/            # green Lot back
```

Every file is exactly 825 x 1125 (The Game Crafter Poker Deck, 2.5" x 3.5" plus
bleed). Faces are 2:3 and the card is 5:7, so they are **frame-fit** - scaled
uniformly into the safe zone on a mat sampled from the face's own border - never
stretched or cropped. Regenerate after any card changes.

## Quick Start

Set up the environment once (`tools/daily_pipeline.py` no longer exists; the
pipeline is the module CLI):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e 'package[test]'
export HYPERTEXT_PY="$PWD/.venv/bin/python" HYPERTEXT_HX="$PWD/.venv/bin/hypertext"
```

1. **Plan a card**:
   ```bash
   .venv/bin/python -m hypertext.pipeline.daily --phase plan --series series/2026-Q1 --auto
   ```
2. **Render, gate and grade** (rebuild -> stamp -> gates -> 3-vote grade -> fix-mode):
   ```bash
   REGEN=1 scripts/pipeline/selfheal.sh 001-grace
   ```
3. **Audit the set**:
   ```bash
   .venv/bin/python -m hypertext.cli lemma-audit   --series series/2026-Q1
   .venv/bin/python -m hypertext.cli ability-audit --series series/2026-Q1
   .venv/bin/python -m hypertext.cli axis-audit    --series series/2026-Q1
   .venv/bin/python -m hypertext.cli art-audit     --series series/2026-Q1
   ```
4. **Prepare for print** (writes `series/2026-Q1/tgc_prep/`, then commit it):
   ```bash
   .venv/bin/python -m hypertext.tgc prep --cards-dir series/2026-Q1/cards
   ```
   Upload one batch folder at a time to The Game Crafter, plus each deck's back.

## Documentation

- [Prompt Recipe](docs/prompt-recipe.md) - Rules for generating card.json
- [Rules of Play](docs/rules.md) - Official game rules
- [FAQ](docs/faq.md) - Common questions

## Card Types

| Type | Description |
|------|-------------|
| NOUN | Person, place, or thing |
| VERB | Action word |
| ADJECTIVE | Descriptive word |
| NAME | Proper name |
| TITLE | Wild card (substitutes for NOUN/NAME) OR collect as own suit (double points) |

## Rarity System

| Rarity | Icon | Ability Pattern |
|--------|------|-----------------|
| COMMON | White circle | Simple ability |
| UNCOMMON | Green square | Suit-based ability |
| RARE | Gold hexagon | References stats |
| GLORIOUS | Orange rhombus | Unique/Combo effects |

## Watermarking

Cards are signed using a cryptographic watermark (SVG sigil + burned into PNG).
- **Key**: `HYPERTEXT_SIGNING_KEY` (env var)
- **Format**: 5x5 grid encoding HMAC-SHA256 signature of card identity
- **Tools**: `tools/watermark.py` (generate), `tools/apply_watermark.py` (burn), `tools/verify_watermark.py` (check)

## Roadmap

See [ROADMAP.md](ROADMAP.md) for development phases.

## License

See [LICENSE](LICENSE) for details.
