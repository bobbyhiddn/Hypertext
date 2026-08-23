# REQ-PPAUG-029 full-card Gemini regeneration

Status: blocked before the first image request on 2026-08-23.

The replacement generator uses `hypertext.pipeline.daily.build_prompt_text` and
`hypertext.gemini.style.generate_with_styles`, with the approved composed
type/rarity template as reference image 1. It requests
`gemini-3.1-flash-image`, portrait `2:3`, Gemini `2K`, image-only output. It does
not draw, composite, or overlay any visible card-face pixels. Pillow is used
only by the separate montage presentation step.

`GEMINI_API_KEY` and `GEMINI_TEXT_API_KEY` were both absent from the execution
environment. The first candidate stopped before an API request, so there are
zero new outputs, no quota consumption, no montage, and no visual QA result.
The rejected REQ-PPAUG-028 images remain excluded from the generation inputs;
only their canonical structured card records are read.

Scheduled automation remains disabled. Nothing was merged, published,
deployed, or reactivated.
