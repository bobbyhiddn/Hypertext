# Hypertext Package

Biblical word-study trading card game toolkit.

## Installation

```bash
cd package
pip install -e .
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `python -m hypertext.pipeline.daily` | Main card generation pipeline |
| `python -m hypertext.tgc prep` | Prepare cards for TGC upload |
| `python -m hypertext.tgc print` | Export print-ready PDFs |
| `python -m hypertext.lots.generation` | Generate phase/lot cards |
| `python -m hypertext.utils.image` | Convert JPEG to PNG |

---

## Modules

### Pipeline (`hypertext.pipeline.daily`)

Main card generation pipeline with multiple phases.

```bash
# Generate demo cards (full pipeline)
python -m hypertext.pipeline.daily --phase demo --cards-dir demo_cards --parallel 4

# Individual phases
python -m hypertext.pipeline.daily --phase plan --cards-dir demo_cards
python -m hypertext.pipeline.daily --phase art --cards-dir demo_cards
python -m hypertext.pipeline.daily --phase composite --cards-dir demo_cards
python -m hypertext.pipeline.daily --phase grade --cards-dir demo_cards

# Rebuild cards that failed grading
python -m hypertext.pipeline.daily --phase rebuild-failed --cards-dir demo_cards
```

**Phases:**
- `plan` - Generate card content (word, gloss, ability, stats, trivia)
- `art` - Generate card artwork via Gemini
- `composite` - Combine template + art + text into final card
- `grade` - Quality check cards against rubric
- `demo` - Full pipeline for demo cards
- `rebuild-failed` - Re-run pipeline for cards that failed grading

---

### TGC Integration (`hypertext.tgc`)

Tools for The Game Crafter manufacturing and local printing.

```bash
# Prepare cards for manual TGC upload (batches of 25)
python -m hypertext.tgc prep --cards-dir demo_cards

# Export print-ready PDFs for Office Depot
python -m hypertext.tgc print --cards-dir demo_cards
python -m hypertext.tgc print --cards-dir demo_cards --output playtest.pdf

# Upload via API (requires TGC credentials)
python -m hypertext.tgc upload --cards-dir demo_cards --dry-run
```

**Print Output:**
- `playtest_prep/card_deck.pdf` - Main deck cards (9 per page, double-sided)
- `playtest_prep/lot_deck.pdf` - Phase/lot cards (9 per page, double-sided)

**Environment Variables:**
```bash
TGC_API_KEY=your_api_key
TGC_USERNAME=your_username
TGC_PASSWORD=your_password
```

---

### Lots/Phase Cards (`hypertext.lots.generation`)

Generate and manage phase (lot) cards.

```bash
# Initialize lot content template
python -m hypertext.lots.generation --phase init --series series/2026-Q1

# Generate flavor text and context via Gemini
python -m hypertext.lots.generation --phase generate --series series/2026-Q1

# Render lot card images
python -m hypertext.lots.generation --phase render --series series/2026-Q1 --parallel 4

# Render with quality grading and retry
python -m hypertext.lots.generation --phase render --series series/2026-Q1 --review

# Force rebuild all with grading
python -m hypertext.lots.generation --phase rebuild --series series/2026-Q1

# Full pipeline (init + generate + render)
python -m hypertext.lots.generation --phase batch --series series/2026-Q1

# Export for manufacturing
python -m hypertext.lots.generation --phase export --series series/2026-Q1 --target thegamecrafter

# Grade existing cards
python -m hypertext.lots.generation --phase grade --series series/2026-Q1
```

**Export Targets:** `playingcards`, `makeplayingcards`, `thegamecrafter`

---

### Card Utilities (`hypertext.cards`)

Individual card processing tools.

```bash
# Validate card JSON against schema
python -m hypertext.cards.validate path/to/card.json

# Composite card from components
python -m hypertext.cards.composite \
  --template raw_template.png \
  --art art.png \
  --card-json card.json \
  --out output.png

# Polish card (remove bracket artifacts)
python -m hypertext.cards.polish input.png output.png
```

---

### Gemini Integration (`hypertext.gemini`)

Google Gemini API wrappers for text, image, and review.

```bash
# Generate image from prompt
python -m hypertext.gemini.image --prompt "A golden chalice" --out chalice.png

# Generate text
python -m hypertext.gemini.text --prompt "Explain the word 'shalom'"

# Review card quality
python -m hypertext.gemini.review --card-dir path/to/card --threshold 85

# Style-referenced image generation
python -m hypertext.gemini.style \
  --prompt-file prompt.txt \
  --style template.png \
  --style example1.png \
  --out output.png
```

**Environment Variables:**
```bash
GEMINI_API_KEY=your_api_key
GEMINI_IMAGE_MODEL=gemini-3-pro-image-preview  # optional
GEMINI_TEXT_MODEL=gemini-3-pro-preview          # optional
```

---

### Watermark (`hypertext.watermark`)

Cryptographic watermarking for card authenticity.

```bash
# Apply watermark to card
python -m hypertext.watermark.apply --card-dir path/to/card

# Verify watermark
python -m hypertext.watermark.verify --card-dir path/to/card
```

---

### Image Utilities (`hypertext.utils.image`)

Image format conversion.

```bash
# Convert single file (deletes original)
python -m hypertext.utils.image image.jpg

# Convert all JPEGs in directory
python -m hypertext.utils.image ./my_folder

# Keep original files
python -m hypertext.utils.image ./my_folder --keep
```

---

### Gallery (`hypertext.gallery`)

Static gallery site generation.

```bash
# Build gallery site
python -m hypertext.gallery.builder --series series/2026-Q1 --out-dir docs/gallery
```

---

## Card Specifications

### Dimensions
- **Card size:** 1024 x 1536 pixels
- **Print size:** 825 x 1125 pixels (300 DPI with bleed)
- **Safe zone:** 753 x 1053 pixels

### Color Palette
| Color | Hex | Usage |
|-------|-----|-------|
| Navy | `#0B1F3B` | Borders, headers |
| Gold | `#C9A44C` | Accents, rare |
| Parchment | `#F3E7C8` | Background |
| Ink | `#111111` | Text |
| Orange | `#F28C28` | Glorious rarity |
| Green | `#2E8B57` | Uncommon rarity |

### Card Types
- **NOUN** - Person, place, thing, concept
- **VERB** - Action or state
- **ADJECTIVE** - Descriptive word
- **NAME** - Proper noun
- **TITLE** - Wild card (substitutes for NOUN or NAME)

### Rarities
| Rarity | Icon | Activation Cost |
|--------|------|-----------------|
| COMMON | White diamond | Reveal only |
| UNCOMMON | Green square | Discard 1 |
| RARE | Gold diamond | Discard 2 |
| GLORIOUS | Orange hexagon | Discard 3 |

---

## Directory Structure

```
series/2026-Q1/
├── cards/
│   ├── 001-word/
│   │   ├── card.json          # Card data
│   │   ├── prompt.txt         # Art generation prompt
│   │   ├── meta.yml           # Metadata
│   │   ├── grade.json         # Quality grade
│   │   └── outputs/
│   │       └── card_1024x1536.png
│   └── ...
├── lots/
│   ├── lot_content.yml        # Flavor/context for all lots
│   ├── 01-remnant/
│   │   ├── meta.yml
│   │   ├── grade.json
│   │   └── outputs/
│   │       └── lot_1024x1536.png
│   └── ...
├── exports/
│   └── tabletopsimulator/
│       └── Hypertext.json
└── stats.yml                  # Series metadata
```

---

## Quality Grading

Cards are graded on a 100-point scale:

| Category | Points | Checks |
|----------|--------|--------|
| Formatting | 35 | Number format, title case, stat ranges |
| Text Clarity | 30 | No garbled text, proper verses |
| Art Quality | 20 | Style match, no artifacts |
| Content Alignment | 15 | Stats match card type expectations |

**Pass threshold:** 90 points with 0 style mismatches

---

## Dependencies

```
google-genai      # Gemini API
Pillow            # Image processing
pyyaml            # YAML parsing
requests          # HTTP (TGC)
python-dotenv     # Environment variables
jsonschema        # Card validation
markdown          # Gallery generation
```

Install all:
```bash
pip install google-genai Pillow pyyaml requests python-dotenv jsonschema markdown
```
