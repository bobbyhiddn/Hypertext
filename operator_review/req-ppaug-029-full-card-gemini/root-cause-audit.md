# REQ-PPAUG-029 root-cause audit

Final acceptance: **PASS after regeneration and image-to-manifest visual
verification of every current face.**

## Correction history

The first claimed replacement was rejected correctly. Direct raster inspection
showed that cards 012–060 still contained stale synthetic content even though
adjacent prompt, request, and manifest files named canonical Babel sources.
Input metadata alone did not prove that a matching raster had been generated.

The resumed build regenerated all 60 current faces through the repository's
native Gemini full-card path, with the corrected SEE v4 pilot locked as the
visual benchmark. Full-resolution review then found one remaining raster
defect: card 023 dropped the separator before each reference carried onto its
second line. Native correction attempts and their source hashes were archived.
A fresh native full-face generation with explicit compact two-line reference
geometry produced the accepted face with four internal bullets in each block,
no leading list markers, two blank Glorious cost icons, and unchanged canonical
content and symbolic tower art.

## Original divergence

1. REQ-PPAUG-028 invented 15 example words and reused unrelated language,
   verse, ability, stat, and theme data across the 5×4×3 matrix. All 60 faces
   were therefore semantically affected.
2. The older 60-card builder rotated decorative Hebrew/Greek pairs
   independently of the English headword instead of preserving the deliberate
   lexeme pair attached to each canonical record.
3. The first replacement changed the renderer but continued to trust the
   synthetic manifest. Later metadata edits were not coupled to raster hashes,
   so stale faces could appear to have corrected inputs.
4. The earlier path pasted visible content over templates. The accepted path
   uses templates only as structural image references and returns one complete
   Gemini raster with no visible-pixel composition or overlay.

## Authoritative projection

Contract v1 selects three reviewed Babel records for each Word type and
projects 17 fields byte-for-byte: word, gloss, type, art sense, ability, three
stats, both verse lines, Hebrew/Aramaic and Greek lexemes and transliterations,
both reference lists, and trivia. The three records repeat only across rarity;
rarity, number, and output-series identity are the matrix-owned fields.

Each source projection has a frozen SHA-256 digest. A canonical source edit
therefore fails validation and requires a deliberate contract version change.
The audit excludes two known source defects instead of copying them:

- `027-hunter`: Greek `θήρα` denotes a hunt/catch or prey, not the represented
  agent noun “hunter.”
- `013-remember`: Greek `μνάομαι` is not the New Testament remember lemma for
  the represented sense.

## Prevention and final evidence

`schema/word_example_generation_contract.v1.json` owns source selection and
field ownership. `hypertext.cards.example_contract` constructs and validates
the exact projection. The generator embeds canonical JSON plus character,
punctuation, reference-bullet, type, rarity, cost, stat, Languages-layout, and
no-portrait contracts; it records every input and output hash and refuses to
release a montage from partial, stale, or visually unaccepted records.

`validation-report.json` passes 60 records, 60 unique rasters, all 20
type/rarity cells, bundle/reference hashes, native Gemini metadata, image
dimensions, human review, and montage binding. `qa-summary.json`, the 20 files
under `review-sheets/`, and `review-montage-by-type-rarity.png` record the final
visual disposition. The focused contract, descriptor, and Gemini image suites
pass 131 tests.
