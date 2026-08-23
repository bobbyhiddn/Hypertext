# REQ-PPAUG-029 full-card Gemini regeneration

Status: 60 contract-v1 candidates generated; ready for operator visual review.

The replacement generator uses `hypertext.pipeline.daily.build_prompt_text` and
`hypertext.gemini.style.generate_with_styles`, with the approved composed
type/rarity template as reference image 1. It requests
`gemini-3.1-flash-image`, portrait `2:3`, Gemini `2K`, image-only output. It does
not draw, composite, or overlay any visible card-face pixels. Pillow is used
only by the separate montage presentation step.

A securely credentialed direct run produced 60 corrected individual Gemini
candidates and adjacent generation records. Candidate 011 was archived after
its noncanonical input was detected, then regenerated from the contract-v1
EARTH projection. The labeled montage was rebuilt from the complete validated
manifest. Final acceptance remains an operator visual decision because Gemini
may still render imperfect text or glyphs. The rejected REQ-PPAUG-028 images
remain excluded from generation inputs; only canonical structured card records
are read.

Scheduled automation remains disabled. Nothing was merged, published,
deployed, or reactivated.
