---
name: hypertext-card-pipeline
description: Use when planning, generating, revising, rebuilding, validating, reviewing, or visually approving Hypertext Word cards through the supported package pipeline and its canonical type-by-rarity template and reference-pack contracts.
---

# Hypertext card pipeline

Use this workflow for Word cards. Work in a dedicated branch and card directory; never experiment in a live series checkout or an in-flight proof.

Choose only the sections needed:

- New card: Setup → Preflight → Plan → Generate → Review and approve.
- Change card data or make a bounded visual fix: Revise → Review and approve.
- Make a fresh raster from an existing recipe: Rebuild → Review and approve.
- Inspect an existing raster without Gemini: Offline visual gate.

## Setup

Run from the repository root with Python 3.10 or newer. Create a Linux/macOS virtual environment; a copied Windows `.venv` is not usable on Linux.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e 'package[test]'   # [test] adds pytest for the contract suite
.venv/bin/python -m hypertext.pipeline.daily --help
```

The batch scripts read `HYPERTEXT_PY` and `HYPERTEXT_HX`; point both at this venv:

```bash
export HYPERTEXT_PY="$PWD/.venv/bin/python" HYPERTEXT_HX="$PWD/.venv/bin/hypertext"
```

Planning needs `GEMINI_TEXT_API_KEY` or `GEMINI_API_KEY`. Full-card generation and automated review need `GEMINI_API_KEY`; watermarking needs `HYPERTEXT_SIGNING_KEY`. Supply secrets through the environment, never command arguments, prompts, logs, or committed files. Model defaults and supported overrides live in [package/hypertext/gemini/config.py](package/hypertext/gemini/config.py); dependencies and the installed entry point live in [package/pyproject.toml](package/pyproject.toml).

## Supported entry points

The card workflow is the module CLI:

```bash
.venv/bin/python -m hypertext.pipeline.daily --help
```

The installed `hypertext` command is supported for the offline pip gate:

```bash
.venv/bin/hypertext visual-gate --help
```

Do not use `hypertext generate`, `hypertext demo`, `hypertext review`, `hypertext gallery`, `hypertext watermark`, or `hypertext lot`; they are advertised Click commands that raise `NotImplementedError`. `python -m hypertext` exposes the same group. Do not use the missing `tools/daily_pipeline.py` commands in the root README.

The package README examples for daily phases `art` and `composite` and its `--cards-dir` flag do not match the current parser. Use `--phase imagegen` with `--series` as documented below and trust current `--help` plus code over those stale examples.

Treat `python -m hypertext.gemini.style` as an internal worker. The pipeline is responsible for creating and validating its serialized reference pack. Path-only `--style`, daily `--style-ref`, and daily `--extra-ref` inputs are legacy or explicitly rejected for full-card work. The supported boundaries are visible in [package/hypertext/cli.py](package/hypertext/cli.py) and [package/hypertext/pipeline/daily.py](package/hypertext/pipeline/daily.py).

## Preflight

Verify the immutable 20-cell package before any live call:

```bash
.venv/bin/python tools/verify_template_package.py
```

Stop if this fails. It verifies the exact type×rarity mapping, paths, PNG contract, dimensions, digests, source lineage, and pending-human-review status. See [tools/verify_template_package.py](tools/verify_template_package.py) and [templates/card/v001/composed/persistence-manifest.json](templates/card/v001/composed/persistence-manifest.json).

Confirm the target series has `deck/queue.yml`, `stats.yml`, and `cards/`. Perform generation only on a review branch. The maintained workflow is manual-only in [.github/workflows/daily-hypertext.yml](.github/workflows/daily-hypertext.yml).

## Plan and assemble the canonical recipe

For a production plan, use `--auto`:

```bash
.venv/bin/python -m hypertext.pipeline.daily --phase plan --series series/2026-Q1 --auto
```

The planner selects an incomplete queue entry using deck distribution, or adds one when all entries are complete. It then:

1. derives the word's semantic identity without rarity;
2. shapes a candidate against the explicit rarity budget;
3. deterministically validates vocabulary, actions, operands, clarity, semantic evidence, and printed power;
4. requires a fresh independent critic to pass every category;
5. locks that exact ability while grounded metadata is generated;
6. overlays the result onto `templates/card_prompt_template.json`; and
7. serializes the canonical visual-descriptor prompt to `card.json`, `prompt.txt`, `meta.yml`, `post.md`, and `revise.txt`.

No validated candidate after three attempts is a hard failure. A queue-provided `ability` is a legacy exact override and bypasses this generation/validation path; do not use it when a newly validated ability is required. Omitting `--auto` enters the canned MAGI fallback and is not a production planning shortcut. Read [package/hypertext/cards/abilities.py](package/hypertext/cards/abilities.py), [package/hypertext/cards/visual_descriptors.py](package/hypertext/cards/visual_descriptors.py), and [docs/rules.md](docs/rules.md) for the executable contracts.

After planning, point `CARD_DIR` at the printed output directory and run the card diagnostic with an absolute path so schema discovery reaches the repository root:

```bash
CARD_DIR="$PWD/series/2026-Q1/cards/NNN-word"
.venv/bin/python -m hypertext.cards.validate "$CARD_DIR/card.json"
```

Stop on errors. This validator currently also exposes any drift between `templates/card_prompt_template.json` and `schema/hypertext_card.schema.json`; do not turn a skipped schema lookup into a pass. See [package/hypertext/cards/validate.py](package/hypertext/cards/validate.py).

## Resolve templates and references

Every full-card operation resolves exactly one cell from the closed five-type × four-rarity manifest in [templates/card/v001/composed/manifest.json](templates/card/v001/composed/manifest.json). [package/hypertext/cards/template_matrix.py](package/hypertext/cards/template_matrix.py) requires operator-accepted status, matching visible labels, a canonical composed path, and the recorded SHA-256. Unknown or missing cells, legacy/base/SEE paths, and digest drift fail without fallback.

The generated `outputs/reference-pack.json` is the only style-input contract:

- Fresh generation: canonical template at position 1, followed by up to three eligible examples.
- Fix revision: content-addressed snapshot of the current card at position 1, canonical template at position 2, then examples.
- Examples must be accepted, finished, nonlegacy, nonsuperseded, exact type×rarity matches with verified image, recipe, prompt, metadata, review evidence, and manifest hashes.
- Eligible examples are ranked by art tokens (35%), semantic content (30%), serialized prompt (20%), and stat proximity (15%), with deterministic digest/path tie-breaks. No eligible example means template-only generation; a missing or invalid template still stops the run.

The curated allowlist is [templates/card/v001/finished-card-references.json](templates/card/v001/finished-card-references.json); selection, ordering, snapshots, and validation are implemented in [package/hypertext/gemini/reference_pack.py](package/hypertext/gemini/reference_pack.py).

## Generate a fresh card

Generate the newest recipe in the series that has no output image:

```bash
.venv/bin/python -m hypertext.pipeline.daily --phase imagegen --series series/2026-Q1
```

`imagegen` has no per-card targeting contract; `--card-dir` is ignored for this phase. Ensure the intended card is the newest missing output, or use `rebuild` on an explicit card directory. The pipeline validates the reference pack, Gemini MIME/decoding/dimensions, and the template-relative stat pips before and after watermarking. It atomically publishes a normalized 1024×1536 PNG and writes provenance. `--phase full` is only plan plus image generation; it does not replace grading or human approval.

## Revise

Edit the generated `revise.txt`. Prefer `Rarity_Change_Request`, `Ability_Change_Request`, or `Stats_Change_Request`; `General_Revision_Request` intentionally unlocks the broader content allowlist. Then run:

```bash
.venv/bin/python -m hypertext.pipeline.daily --phase revise --card-dir "$CARD_DIR" --revise-file "$CARD_DIR/revise.txt"
```

The model may return only `add` or `replace` JSON Patch operations on paths unlocked by the form. With an existing image and `Rebuild: false`, revision uses fix-mode reference ordering. Set `Rebuild: true` for a fresh image that does not reference the current raster. Avoid inline `--revision` and `--image-only` for controlled production edits; the file form is the bounded, workflow-backed contract. Re-run every gate after any revision.

## Rebuild

Rebuild preserves `card.json` and makes a fresh raster with template-first references:

```bash
.venv/bin/python -m hypertext.pipeline.daily --phase rebuild --card-dir "$CARD_DIR"
```

If `card.json` changed, rebuild the canonical prompt too:

```bash
.venv/bin/python -m hypertext.pipeline.daily --phase rebuild --card-dir "$CARD_DIR" --regen-prompt
```

Rebuild is not a repair waiver. It must pass the same reference, image, pip, provenance, automated-review, and human gates.

## Provenance and automated review

Run the offline pip gate without Gemini:

```bash
.venv/bin/hypertext visual-gate --card-dir "$CARD_DIR"
```

Then grade the existing image against the canonical references and exact 100-point quality contract:

```bash
.venv/bin/python -m hypertext.pipeline.daily --phase grade --card-dir "$CARD_DIR" --style-series series/2026-Q1
```

`grade` calls Gemini but does not intentionally regenerate the card. The package README's 90-point threshold is stale; the executable quality gate requires every dimension to reach 100. `--phase review` is an active iterative path that may rebuild or revise the raster; use it only when that mutation is wanted, and restart visual approval afterward.

Before approval, bind the final raster to these records:

- `outputs/generation.json`: model, source MIME, normalized dimensions, attempts, reference count, and output digest.
- `outputs/reference-pack.json`: ordered, labeled, hash-verified inputs and candidate audit.
- `outputs/generation-provenance.json` and `outputs/generation.log`: recipe, prompt, request settings, references, and output lineage.
- `outputs/quality-provenance.json`: bounded stage results.
- `outputs/visual-gate.generated.json` and `outputs/visual-gate.json`: pre- and post-finalization pip evidence.
- `grade.json` and `grade.txt`: automated verdict and corrections.

The exact gate semantics are in [package/hypertext/gemini/image_contract.py](package/hypertext/gemini/image_contract.py), [package/hypertext/cards/stat_pip_gate.py](package/hypertext/cards/stat_pip_gate.py), and [package/hypertext/quality.py](package/hypertext/quality.py).

## Human visual approval

Automated success is necessary, never sufficient. A human must inspect the final full-resolution PNG beside its exact canonical template and the selected references named in `reference-pack.json`. Verify identity and all printed facts, type/rarity treatment, 15 pips and filled counts, English/Greek/Hebrew legibility, verse and trivia fidelity, relevant art, frame geometry, and absence of invented text, brackets, artifacts, or style drift.

Record an explicit pass/fail in the review branch or its operator-review evidence. Any change to the raster, recipe, prompt, reference pack, or template invalidates the prior verdict. Do not merge, publish, deploy, or re-enable scheduling without explicit operator approval; there is no CLI flag that grants it. Follow the qualitative gates in [docs/gemini-migration-evaluation.md](docs/gemini-migration-evaluation.md) and the accepted evidence shape in [operator_review/req-ppaug-029-full-card-gemini/README.md](operator_review/req-ppaug-029-full-card-gemini/README.md).

## Prepare for print (The Game Crafter)

Once every card in the set passes, build the print set. It is committed with the
set at `series/<id>/tgc_prep/`, so the exact files sent to the printer stay
recoverable for any past state:

```bash
.venv/bin/python -m hypertext.tgc prep --cards-dir series/2026-Q1/cards
```

It reads each card's `outputs/card_1024x1536.png`, auto-detects the sibling
`lots/` (a flat PNG package, not per-card folders), and writes both decks in
25-card upload batches plus each deck's back - `templates/card_back.png` for
Words, `templates/lots/Lot_Back.png` for Lots. Every file is exactly
825 x 1125: the 2:3 face is **frame-fit** into the 5:7 card, scaled uniformly
onto a mat sampled from its own border, never stretched or cropped
(`package/tests/test_tgc_frame_fit.py` holds that contract).

Regenerate after any card changes and commit the result. Product and upload
details are in [docs/How-To-TGC.md](docs/How-To-TGC.md) and
[docs/printing.md](docs/printing.md).

## Fail closed

- Stop on missing inputs, invalid type/rarity, manifest or hash drift, invalid reference roles, corrupt/wrong-size Gemini output, safety/no-image responses, pip defects, style mismatch, timeout, or any quality dimension below 100.
- Never substitute a legacy, base, type-only, rarity-only, SEE, rejected, superseded, series, or arbitrary path reference for the canonical cell.
- Never reuse a rejected ability draft or an unverified queue ability as though it passed the explicit validator and critic.
- Do not edit templates to make a candidate pass, and do not treat deterministic pip acceptance as whole-card visual acceptance.
- Keep generation manual and isolated. A successful process exit, `grade.json`, or PR comment does not authorize main-branch inclusion.
