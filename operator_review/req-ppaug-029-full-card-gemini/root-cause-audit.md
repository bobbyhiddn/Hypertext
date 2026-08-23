# REQ-PPAUG-029 root-cause audit

Final acceptance: **pending human review**.

## Divergence

1. **Source data:** REQ-PPAUG-028 did not select Babel records. It invented 15
   example words and reused three unrelated Hebrew/Greek pairs, three verse
   pairs, synthetic abilities, statistics, and semantic themes across the
   5×4×3 matrix. Consequently all 60 faces were semantically affected.
2. **Historical lexemes:** the original 20-card Example set used one deliberate
   lexeme pair per card. The 60-card path instead rotated decorative lexemes
   independently of each invented headword (for example, HARBOR with
   `שָׁלוֹם`/`σοφία`).
3. **Prompt/reference assembly:** the first 60-card builder rendered with Pillow
   and repository card crops. The initial full-face replacement passed the
   invented REQ-PPAUG-028 manifest through `build_prompt_text`; changing the
   renderer therefore did not correct its inputs.
4. **Template use:** REQ-PPAUG-028 pasted content over composed templates. The
   corrected path retains the consistency gain by supplying the canonical
   composed type/rarity face as Gemini reference 1, followed only by matching
   historical Example faces. The visible result remains a complete Gemini
   raster, with no face overlay or post-generation composition.
5. **Gemini request:** corrected requests use
   `gemini-3.1-flash-image`, portrait `2:3`, `2K`, image-only output through
   `hypertext.gemini.style.generate_with_styles`. Each request records reference
   hashes, canonical source, and input-contract version 1.
6. **Finished output:** every pre-contract face is superseded because every face
   contained approximate semantic content. Regenerated candidates preserve the
   approved type/rarity geometry, white type icons, and Rare/Glorious printed
   costs. Raster text fidelity is an operator-review concern and is not claimed
   as machine-accepted.

## Authoritative projection

Contract v1 selects three defect-free Babel records for each Word type and
projects these 17 fields byte-for-byte: word, gloss, type, art sense, ability,
three stats, both verse lines, Hebrew/Aramaic and Greek lexemes and
transliterations, both testament reference lists, and trivia. The three records
are repeated only across rarity; rarity, number, and output-series identity are
the only face fields changed by this matrix.

Each selected projection also has a frozen SHA-256 digest. A later canonical
source edit therefore fails validation and requires an explicit contract
version/audit decision instead of silently changing regeneration inputs.

The audit identified two canonical Babel source defects and excludes those
records instead of copying them:

- `027-hunter`: Greek `θήρα` is hunt/catch or prey, not the agent noun
  “hunter.”
- `013-remember`: Greek `μνάομαι` is not the New Testament remember lemma for
  the represented sense.

These findings do not silently modify the canonical Babel set; they are gates
on example-source eligibility pending a separate source-data correction.

## Prevention

`schema/word_example_generation_contract.v1.json` is the versioned selection
and field-ownership contract. `hypertext.cards.example_contract` constructs and
validates exact repository projections. The generator embeds one serialized
`EXACT_CANONICAL_CONTENT_JSON` block plus explicit no-translation/no-paraphrase
instructions, records the contract in every request and manifest record, and
refuses to build a montage from a partial or legacy manifest. Tests mutate an
original-language field to prove approximate/decorative content is rejected.

Machine validation establishes input and request fidelity, not legibility of
model-rendered glyphs. Human inspection of every full-resolution candidate is
the final acceptance gate.
