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
├── series/           # Quarterly card series
│   └── 2026-Q1/      # Series root
│       ├── cards/    # Source of truth for each card
│       └── deck/     # Computed stats and queue
├── templates/        # Card generation templates
├── schema/           # JSON validation schemas
├── docs/             # Documentation
└── tools/            # Build and validation scripts
```

## Quick Start

1. **Plan a new card**:
   ```bash
   python tools/daily_pipeline.py --phase plan --series series/2026-Q1 --auto
   ```
2. **Generate Image & Watermark**:
   ```bash
   python tools/daily_pipeline.py --phase imagegen --series series/2026-Q1
   ```
3. **Review & Revise**:
   ```bash
   # If revision is needed, edit revise.txt in the card folder
   python tools/daily_pipeline.py --phase revise --card-dir series/2026-Q1/cards/NNN-word
   ```
4. **Build Gallery**:
   ```bash
   python tools/daily_pipeline.py --phase gallery --series series --out-dir _site
   ```

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
| TITLE | Special/wild card |

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
