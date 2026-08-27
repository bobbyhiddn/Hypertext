# Hypertext Printing Specifications

## Card Dimensions

### Standard Playing Card Size
- Width: 2.5 inches (63.5 mm)
- Height: 3.5 inches (88.9 mm)
- Aspect ratio: 2:3

### Resolution Requirements

| Purpose | DPI | Pixel Dimensions |
|---------|-----|------------------|
| Minimum print | 300 | 750 x 1050 |
| Recommended print | 300 | 1050 x 1575 |
| High quality print | 300 | 2100 x 3150 |
| Current target | ~340 | 1024 x 1536 |

The current 1024 x 1536 resolution provides approximately 340 DPI at final print size, which exceeds the 300 DPI minimum.

### Print-Ready Export
For final print production:
- Upscale to 2048 x 3072 minimum
- Export as PDF with embedded color profile
- Use CMYK color space for offset printing
- Include 1/8" (3mm) bleed on all sides

## Bleed and Safe Zones

```
┌─────────────────────────────┐
│         BLEED ZONE          │  <- 1/8" (3mm) outside cut line
│  ┌─────────────────────┐    │
│  │     CUT LINE        │    │
│  │  ┌───────────────┐  │    │
│  │  │  SAFE ZONE    │  │    │  <- 1/8" (3mm) inside cut line
│  │  │               │  │    │
│  │  │   Keep all    │  │    │
│  │  │   important   │  │    │
│  │  │   content     │  │    │
│  │  │   here        │  │    │
│  │  │               │  │    │
│  │  └───────────────┘  │    │
│  └─────────────────────┘    │
└─────────────────────────────┘
```

## Deck Compilation

### Quarterly Deck Contents
- All cards from the quarter's series
- Divider cards (optional)
- Reference card with game rules (optional)

### File Organization
```
series/2026-Q1/deck/
├── decklist.yml      # Card manifest
├── print-spec.md     # Print job specs
└── export/
    ├── deck_2026Q1_print.pdf
    ├── deck_2026Q1_sheets.pdf  # For sheet printing
    └── cut_guides.pdf
```

### Print Partners

#### Option A: Self-Print and Ship
- Use high-quality cardstock (300+ gsm)
- Laminate or use clear sleeves for durability
- Manual cutting with precision cutter

#### Option B: Print-on-Demand Partners
- MakePlayingCards.com
- DriveThruCards
- The Game Crafter
- PrinterStudio

### Cost Considerations
- 52-card deck typical POD cost: $15-25/deck
- Bulk printing (100+ decks): $8-12/deck
- Subscriber pricing target: $25/month includes quarterly deck

## Quality Checklist

Before sending to print:
- [ ] All cards validated against schema
- [ ] Resolution meets 300 DPI minimum
- [ ] Bleed extended on all cards
- [ ] Text within safe zone
- [ ] Color profile embedded (sRGB or CMYK)
- [ ] Proof printed and reviewed
- [ ] Decklist verified against card files
