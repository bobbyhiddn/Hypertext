# REQ-PPAUG-029 full-card Gemini regeneration

Status: partial and blocked on 2026-08-23.

The replacement generator uses `hypertext.pipeline.daily.build_prompt_text` and
`hypertext.gemini.style.generate_with_styles`, with the approved composed
type/rarity template as reference image 1. It requests
`gemini-3.1-flash-image`, portrait `2:3`, Gemini `2K`, image-only output. It does
not draw, composite, or overlay any visible card-face pixels. Pillow is used
only by the separate montage presentation step.

An earlier securely credentialed run produced 18 fresh individual Gemini
candidates and adjacent generation records before it stopped. Stateless worker
shells still lack both supported Gemini environment variables, so cards 019–060
and replacement attempts cannot be requested. Direct visual QA accepted 12 of
the 18 candidates and rejected six; see `qa-summary.json`. No final montage is
created because the required accepted 60-card set does not exist. The rejected
REQ-PPAUG-028 images remain excluded from generation inputs; only canonical
structured card records are read.

Scheduled automation remains disabled. Nothing was merged, published,
deployed, or reactivated.
