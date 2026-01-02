# Print Specification: 2026 Q1 Deck

## Card Specifications

| Property | Value |
|----------|-------|
| Card size | 2.5 x 3.5 inches (63.5 x 88.9 mm) |
| Bleed | 1/8 inch (3mm) all sides |
| Safe zone | 1/8 inch (3mm) inside cut line |
| Resolution | 300 DPI minimum |
| Color space | sRGB (convert to CMYK for offset) |
| File format | PNG (source), PDF (export) |

## Resolution Targets

| Output | Dimensions |
|--------|------------|
| Digital display | 1024 x 1536 px |
| Print source | 2048 x 3072 px |
| With bleed | 2175 x 3225 px (at 300 DPI) |

## Print-Ready Checklist

Before exporting for print:

- [ ] All cards validated against schema
- [ ] Card count verified against decklist
- [ ] Images upscaled to print resolution
- [ ] Bleed extended on all cards
- [ ] Color profile embedded
- [ ] PDF assembled with cut guides
- [ ] Test print reviewed

## Export Files

```
export/
├── deck_2026Q1_digital.pdf    # Screen resolution
├── deck_2026Q1_print.pdf      # Print resolution, individual cards
├── deck_2026Q1_sheets.pdf     # 9-up sheets for sheet printing
└── cut_guides.pdf             # Cut line reference
```

## Cardstock Recommendations

| Option | Weight | Finish |
|--------|--------|--------|
| Budget | 270 gsm | Matte |
| Standard | 300 gsm | Satin |
| Premium | 350 gsm | Linen |

## Notes

- Export pipeline not yet implemented
- Manual assembly currently required
- See docs/printing.md for detailed specs
