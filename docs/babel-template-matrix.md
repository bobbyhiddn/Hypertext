# Canonical Babel template matrix

This assessment implements REQ-PPAUG-012 and informs REQ-PPAUG-011. It is an offline inventory only: no images were generated and no API quota was used.

The authoritative schema and rules define five word types (`NOUN`, `VERB`, `ADJECTIVE`, `NAME`, `TITLE`) and four rarities (`COMMON`, `UNCOMMON`, `RARE`, `GLORIOUS`). The canonical Babel index contains 31 cards and occupies every member of the 5 × 4 Cartesian product. Therefore Babel has 20 valid type-rarity combinations, zero invalid combinations, and requires 20 final canonical composed templates under the operator's one-template-per-combination requirement.

| Type | COMMON | UNCOMMON | RARE | GLORIOUS | Cards |
|---|---:|---:|---:|---:|---:|
| NOUN | 5 | 1 | 1 | 1 | 8 |
| VERB | 2 | 5 | 3 | 1 | 11 |
| ADJECTIVE | 1 | 1 | 1 | 1 | 4 |
| NAME | 1 | 1 | 1 | 1 | 4 |
| TITLE | 1 | 1 | 1 | 1 | 4 |
| Total | 10 | 9 | 7 | 5 | 31 |

## Structural layers versus canonical outputs

The current v001 package has one shared base, all five type-specific full-canvas references, and all four rarity-specific full-canvas references. These are reusable source layers: type controls the type label/icon and any type typography; rarity controls the exact rarity word, diamond treatment, and bounded ornament. A final canonical template is their deterministic composition for one type plus one rarity, with fixed geometry and approved elements preserved.

Current structural coverage is 5/5 type layers and 4/4 rarity layers. Current final coverage is 0/20 because there is no `composed/TYPE/RARITY` package or equivalent explicit mapping to a checked composed artifact. The exact gaps are every combination listed in the table. There are no duplicate subtype keys, but the base plus nine subtype assets repeat the whole card canvas even though each subtype should own only its bounded concern; this semantic duplication encouraged the incorrect assumptions that type-only and rarity-only canvases were final templates, and that nine subtype variants covered a 20-output requirement.

The package also previously treated `glorious` as exceptional whole-card styling. The visual contract permits only a rarity-layer delta: three gold diamonds and restrained corner filigree, without geometry or panel-fill changes. No type-rarity pair is forbidden by grammar, schema, rules, or canonical data.

## Reconstruction sequence

1. Freeze the accepted base geometry and extract approved elements without generative edits.
2. Normalize five bounded type layers against that base, then four bounded rarity layers.
3. Deterministically compose the 20 outputs in matrix order and validate dimensions, MIME, fixed regions, labels, and iconography.
4. Render representative cards from each combination, then the full 31-card Babel set, using deterministic recomposition; only after offline acceptance consider any separately authorized image generation.

The machine-readable contract is `schema/babel_template_matrix.json`. Its test compares the matrix with the canonical index and fails with card identity when any Babel card lacks a supported mapping.
