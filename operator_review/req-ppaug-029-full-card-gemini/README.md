# REQ-PPAUG-029 full-card Gemini regeneration

Status: **accepted after full-resolution review of all 60 current faces and the
labeled type-by-rarity montage. No cards are blocked.**

## Native generation path

Every visible face is a complete Gemini raster generated through
`hypertext.pipeline.daily.build_prompt_text` and
`hypertext.gemini.style.generate_with_styles`. Requests use
`gemini-3.1-flash-image`, portrait `2:3`, Gemini `2K`, and image-only output.
The composed type/rarity template, the locked SEE v4 pilot, one matching
historical face, and the accepted printed-SEE Languages crop are references;
none is programmatically assembled into the output. Pillow is used only for
review sheets and the montage.

The locked benchmark is
`../req-ppaug-030-see-benchmark/pilot-see-v4/outputs/card_1024x1536.png`.
It controls the restrained printed finish and the compact, equal-width
HEBREW/ARAMAIC and GREEK treatment. Canonical Babel source data controls every
word, lexeme, transliteration, verse, reference, ability, stat, and trivia
field.

## Acceptance evidence

- `provenance.json` binds all 60 current 1024×1536 rasters to their source,
  prompt, request, generation metadata, references, and hashes. Superseded
  card 023 candidates remain hash-addressed in its repair and regeneration
  history.
- `qa-summary.json` records the full-resolution 60-card review and the released
  montage review. `visual-rejections.json` records the final zero-blocker
  disposition.
- `review-sheets/` contains 20 labeled full-resolution sheets, one for each
  type/rarity cell. `review-montage-by-type-rarity.png` contains only the 60
  hash-accepted current faces.
- `validation-report.json` passes 60 records, 60 unique output hashes, all 20
  type/rarity cells at three variants each, bundle/reference hashes, native
  generation metadata, dimensions, human review, and montage binding.

The final visual pass found exact canonical text and reference separators,
compact two-column Languages panels, correct type icons, rarity costs and
stats, and symbolic art without recognizable faces or portrait likenesses.
Card 023 required a fresh native full-face regeneration after image-guided
attempts treated wrapped references as a list; the accepted face has exactly
four internal bullets in each Refs block and no leading list marker.

Scheduled automation remains disabled. Nothing was merged, published,
deployed, or reactivated by this work.
