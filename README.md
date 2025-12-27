# Hypertext

A daily word-study trading card project featuring Biblical Greek and Hebrew terms.

## Overview

Hypertext produces collectible trading cards that explore words from Scripture. Each card includes:
- Original language forms (Greek and Hebrew)
- Scripture references from both Old and New Testaments
- Contextual artwork
- Trivia and linguistic notes

## Repository Structure

```
hypertext/
├── series/           # Quarterly card series
│   └── 2026-Q1/      # Q1 2026 series
│       ├── cards/    # Individual card folders
│       └── deck/     # Compiled deck outputs
├── templates/        # Card generation templates
├── schema/           # JSON validation schemas
├── docs/             # Documentation
└── tools/            # Build and validation scripts
```

## Quick Start

1. **Create a new card**: Copy a card folder template from `series/2026-Q1/cards/`
2. **Fill in metadata**: Edit `meta.yml` with card details
3. **Generate card.json**: Run the generation script or fill manually from template
4. **Validate**: Run `python tools/validate_card.py series/2026-Q1/cards/NNN-word/card.json`
5. **Generate image**: Use card.json as prompt for image model
6. **Commit**: Save outputs and commit

## Documentation

- [Prompt Recipe](docs/prompt-recipe.md) - Rules for generating card.json
- [Style Guide](docs/style-guide.md) - Visual design specifications
- [Printing](docs/printing.md) - Print production specs
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
| GLORIOUS | Orange rhombus | Unique, can reference other cards |

## Roadmap

See [ROADMAP.md](ROADMAP.md) for development phases.

## License

See [LICENSE](LICENSE) for details.
