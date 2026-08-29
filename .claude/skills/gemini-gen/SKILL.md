---
name: gemini-gen
description: Use when generating an image with Gemini that is NOT a Word Card or Lot face - marketing art, a table scene, box art, promo or diagram imagery - especially when the result must match artifacts that already exist. Covers reference-image prompting, aspect ratios, verification, and the traps this project hit.
---

# Gemini image generation (non-card art)

`generate_image.py` in this directory wraps the multi-reference call: a prompt plus labelled
reference images, N candidates, saved to a directory for you to pick from.

**This is not the path for Word Cards or Lot faces.** Those go through the card pipeline
(`hypertext.pipeline.daily`) and the lot pipeline (`hypertext.lots.*`), which apply
deterministic stamping and their own gates. Use this for everything else.

## Run it

```bash
set -a; . ./.env; set +a          # GEMINI_API_KEY
.venv/bin/python .claude/skills/gemini-gen/generate_image.py \
  --prompt-file /tmp/scratch/prompt.txt \
  --out-dir /tmp/scratch/art \
  --ref series/2026-Q1/cards/024-covenant/outputs/card_1024x1536.png:"a Word Card face, GLORIOUS" \
  --ref templates/card_back.png:"the card BACK, navy and gold" \
  --ref series/2026-Q1/lots/faces/02-pentateuch.png:"a LOT card face" \
  --aspect 4:3 --attempts 3 --stem table
```

Then **look at all three** and pick. Do not accept the first one unseen.

## The one rule that matters

**Show, don't describe.** A prompt describes; a reference image shows. When the output must
match something that already exists, pass that thing as a reference and tell the model to copy
it.

This cost a full afternoon to learn. A Lot card had the wrong TITLE icon. Three rounds of prose
- "light outline picture frame", "medium-weight outline, neither solid nor hairline" - produced a
plain rectangle every time, because the set's real glyph is an *ornate scrolled frame* and no
adjective conveys that. Passing two correct cards as reference images fixed it on the second
attempt. Label each reference so the model knows what it is looking at; an unlabelled image is
ambiguous.

## Verifying the result

Three numeric gates were built to judge that icon - ink coverage, glyph overlap (IoU), pixel
drift - and **all three disagreed with the eye**:

| Metric | How it failed |
|---|---|
| Ink coverage | Passed the wrong plain rectangle at 0.174; rejected the correct ornate frame at 0.255 |
| Glyph IoU | 0.12-0.28 across cards that were all correct - no separation at all |
| Pixel drift | Rejected three correct repairs: an image model re-renders rather than edits, so two renders of identical content differ as much as two unrelated images |

So: automate what is genuinely mechanical (is the file the right size, does it contain the
expected strings, are the required elements present) and **look at the rest**. Build a contact
sheet and read it:

```bash
.venv/bin/python scripts/pipeline/contact_sheet.py out.jpg <slug>...   # for cards
```

For arbitrary images, tile the candidates into one JPEG and view that - comparing side by side
catches what viewing one at a time does not.

**Verify content with a vision call, not with pixels.** `scripts/pipeline/lot_gates.py`
`check_content` is the pattern: ask the model to transcribe the printed fields, then compare the
transcription to your record deterministically. That catches a placeholder verse or a garbled
line, which is what actually goes wrong.

## Prompt notes that worked here

- **Put the hard constraints first and in caps.** "ABSOLUTELY NO FACES AND NO PEOPLE ABOVE THE
  WRIST" held across every attempt; a polite clause buried mid-prompt does not.
- **Say what is in frame, positionally.** "CENTRE: a face-down draw pile ... FOUR PLAYER SEATS,
  one at each edge" gives a composition. "A game in progress" gives a lottery.
- **Name the medium in the project's own words.** Reusing the set's own style clause - luminous
  cinematic oil painting, impressionistic brushwork, saturated blues and golds, one warm light
  source - keeps promo art in the same world as the cards.
- **Let text be illegible.** Asking for real words on small painted cards produces garbage;
  "card text may be suggested with soft illegible marks" reads better and avoids the failure.
- **Exclude furniture explicitly**: no text overlays, no title, no logo, no watermark, no UI.

## Aspect ratio

`--aspect` is free here (4:3, 16:9, 1:1, 2:3). Note that
`hypertext.gemini.image_contract.validate_request` pins **2:3 at 2K** - that contract governs
card faces, and this script deliberately does not go through it, because promo art is not a card.

## Cost and etiquette

Each attempt is a full image generation. Three candidates is usually right: one is a coin flip,
three lets you choose. Prefer fixing the prompt over raising `--attempts`. The key lives in
`.env` (gitignored) - never echo it, never pass it as an argument, and rotate it when a
generation push concludes.
