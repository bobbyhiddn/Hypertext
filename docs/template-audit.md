# Curated template audit

Audit date: 2026-08-22. Status: queued for regeneration; no assets regenerated and no API calls made. All assets below are face references. Card backs (`templates/card_back*.png` and `templates/lots/Lot_Back.png`) are output/export references, not generator templates, and were checked for role confusion but are not queued.

The current generation contract is PNG, 1024×1536, portrait 2:3, with deterministic typography/layout applied by the card or Lot renderer. The checked versioned assets predate that normalized output contract.

| Family | Checked subtype | Result and exact reason |
|---|---|---|
| Card | base | Flagged: 848×1264; JPEG bytes with `.png` extension |
| Card | common | Flagged: 848×1264 |
| Card | uncommon | Flagged: 848×1264; JPEG bytes with `.png` extension |
| Card | rare | Flagged: 848×1264 |
| Card | glorious | Flagged: 848×1264 |
| Card | noun | Flagged: 848×1264; JPEG bytes with `.png` extension |
| Card | verb | Flagged: 848×1264; JPEG bytes with `.png` extension |
| Card | adjective | Flagged: 848×1264; JPEG bytes with `.png` extension |
| Card | name | Flagged: 848×1264; JPEG bytes with `.png` extension |
| Card | title | Flagged: 848×1264 |
| Lot | base | Flagged: 848×1264; JPEG bytes with `.png` extension; prompt uses plural `X-CARDS` and bracketed visible type labels |
| Lot | 5-card | Flagged: 848×1264; JPEG bytes with `.png` extension; prompt requires bracketed visible type labels |
| Lot | 6-card | Flagged: 848×1264; JPEG bytes with `.png` extension; prompt requires bracketed visible type labels |
| Lot | 7-card | Flagged: 848×1264; JPEG bytes with `.png` extension; prompt requires bracketed visible type labels |

Definition audit also found `templates/card/meta.yml` points to v004 while the complete curated subtype set is in v001. The manifest preserves this finding without changing version selection. Typography and layout definitions otherwise agree on the serif/navy/gold face contract; corrected assets must still pass the offline contract before their flags clear.

Offline status command: `PYTHONPATH=package python -m hypertext.pipeline.template --type card --phase audit` (repeat with `--type lot`). Regeneration command per queued entry: `PYTHONPATH=package python -m hypertext.pipeline.template --type FAMILY --phase refine --subtype SUBTYPE --target-version 1`. Cron remains disabled.
