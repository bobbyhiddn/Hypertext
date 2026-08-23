# REQ-PPAUG-028 — Hypertext Example Set

This review package contains exactly 60 finished portrait Word Cards: three examples for every cell in the approved 5-type × 4-rarity matrix. `cards/` contains the individual PNGs on the approved templates' native 848×1272 canvas (the source filenames retain a legacy `1024x1536` label). `review-montage-by-type-rarity.png` is grouped by type in rows and rarity in Common, Uncommon, Rare, Glorious order, with three adjacent variants per rarity.

`provenance.json` records structured content, approved template, generated art source, model/composition route, prompt, dimensions, hashes, and native cost requirements per card. `template-fingerprints.json` protects the approved structural sources. Run `python scripts/validate_word_example_set.py`; its machine-readable result is `validation-report.json`.

Schedule and automation remain disabled. This package is evidence for human visual review, which remains the acceptance gate.
