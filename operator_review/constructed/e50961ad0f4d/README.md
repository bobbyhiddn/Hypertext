# REQ-PPAUG-024 Word Card source collage

`visual_acceptance_review_5x4.png` replaces the rejected generated matrix review. It is a read-only source-reference collage containing only the 11 native Word Card template faces and 20 completed example-card faces visible in the operator authority sheet `hypertext_templates_e50961ad0f4d_review.png`.

The two sections distinguish native templates from completed samples. Each face is shown whole and has its exact repository-relative path and role directly beneath it. No generated/reconstructed matrix candidate, Lot card, back, palette, or other raster appears in the replacement review artifact.

`visual_acceptance_review_5x4.provenance.json` records the authority commit and Git blob, source-byte SHA-256, source dimensions, full-face scaling operation, rendered-pixel SHA-256, and exact collage bounding box for every face. Run `python3 tools/verify_word_card_source_collage.py` to reconstruct every cell from the listed authority blob and compare all face pixels with the committed collage.

The builder uses Pillow only for deterministic full-face downscaling, placement, and out-of-face labels. It does not use an image model and does not crop, paint over, reinterpret, or approximate a face. The rejected generated candidate files remain historical inputs only and are not part of this review artifact.
