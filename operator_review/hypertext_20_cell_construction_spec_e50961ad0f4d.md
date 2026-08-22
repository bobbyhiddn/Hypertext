# Hypertext exact 20-cell construction specification

## Authority and non-destructive boundary

- Frozen authority: commit `e50961ad0f4d66f398f81706f092a7d0ea9cb0f4` (`20 example cards`).
- All input paths are repository-relative at that commit. Resolve and verify them by Git blob ID, not by the current worktree alone.
- Canonical inputs are read-only. Never overwrite anything under `templates/`.
- Write constructed artifacts only under `operator_review/constructed/e50961ad0f4d/` (or an equivalent disposable review directory outside `templates/`).
- Despite the filenames, the authoritative raster canvas is **848 × 1264 px**. Preserve that exact size, orientation, and pixel registration. Emit lossless RGB/RGBA PNG.

## Shared construction contract

Every cell is the orthogonal composition `BASE + exactly one TYPE + exactly one RARITY`. The base is the sole authority for geometry, border, and typography placement. The type and rarity sources are visual references for the controlled regions; they are not wholesale replacement frames.

Shared geometry and border invariants:

1. Keep the 848 × 1264 canvas and all base landmarks at identical pixel coordinates: navy outer frame, thin gold inset, parchment field, chamfered content framing, navy type pill/circle, centered serif title, italic serif definition, incurved gold art frame, circular stat pips, stacked chamfered ability/verse/language panels, parchment trivia area, and navy footer.
2. Preserve the base border on all four sides and corners. Type must not change any border pixel. Rarity may add only the restrained canonical rare/glorious accent; it must not change frame thickness, move the inset, flood the parchment/content field, or introduce per-example glow/corner drift.
3. Keep the type circle and rarity tab dimensions and positions fixed. Do not move or resize the title, definition, art frame, stat row, panels, language strip, trivia, or footer. Do not change the serif hierarchy.
4. The only type-dependent content is the white icon inside the navy type circle. The only rarity-dependent content is the rarity diamond, its bonus/cost ornament, and the restrained rarity accent shown by the rarity reference.
5. Do not reproduce JPEG artifacts, encoding differences, malformed symbols, baseline drift, or frame differences seen in example cards.

## Inputs and controlled variants

Base:

- `templates/card/v001/base/template_1024x1536.png` — blob `298d816b4b2fba1a249ae725a3cf26f7df75ced2`

Type variants (select exactly one):

| Key | Controlled icon | Reference path | Blob |
|---|---|---|---|
| `noun` | white closed book | `templates/card/v001/noun/template_1024x1536.png` | `a2f073a4915e9de3b7e11a73edbfc8c0b3f0b22f` |
| `verb` | white slanted pencil | `templates/card/v001/verb/template_1024x1536.png` | `860093ebd217df992c188f310f6adaf9a9c91f82` |
| `adjective` | white sparkle pencil with two four-pointed stars | `templates/card/v001/adjective/template_1024x1536.png` | `51337d323ab8a678099315fc10bc9f33522b0bdb` |
| `name` | white feather quill | `templates/card/v001/name/template_1024x1536.png` | `9ef51b1290cc1fa4de96e42f5d8115419523b813` |
| `title` | white ornate empty frame | `templates/card/v001/title/template_1024x1536.png` | `eb90f0d4a240c2569cae71d3cb4fe6dd3ef84cc5` |

Rarity variants (select exactly one):

| Key | Diamond | Bonus/cost ornament | Reference path | Blob |
|---|---|---|---|---|
| `common` | white, navy outline | none | `templates/card/v001/common/template_1024x1536.png` | `7b189da0ad8187dae72399615f9e032f028c5f19` |
| `uncommon` | green `#2E8B57`, navy outline | none | `templates/card/v001/uncommon/template_1024x1536.png` | `bc170f216df5e45d4875b2f5170097ba32d807a2` |
| `rare` | gold `#C9A44C`, navy outline | small `+` and exactly one card icon | `templates/card/v001/rare/template_1024x1536.png` | `c57f280e34ff016e3e579e15b364689a8c010041` |
| `glorious` | orange `#F28C28`, navy outline | small `+` and exactly two card icons | `templates/card/v001/glorious/template_1024x1536.png` | `5adef84efec7fa5ac3855869e6f9f08062cf15c6` |

Supplemental symbol references (validation only):

- `templates/palettes/type_symbols_palette.png` — blob `078be48cf5de2da4460494ee1a1a61a45f4ae04f`
- `templates/palettes/rarity_diamonds_palette.png` — blob `77b370eec358476894a9fe5ec73a4c92e1c901c4`

## Exact output matrix and example witnesses

Each output filename is normative. Metadata/image witness pairs are read-only semantic and visual evidence; do not use a witness as the geometry master.

| Cell | Output path under `operator_review/constructed/e50961ad0f4d/` | Witness metadata path · blob | Witness image path · blob |
|---:|---|---|---|
| 01 | `noun__common.png` | `templates/example_cards/001-grace/meta.yml` · `9908b40ed83d9e6b01d609396d7fbd6099aa5c25` | `templates/example_cards/001-grace/outputs/card_1024x1536.png` · `6e0799ecfb272915757dd421eec1340c9217c33b` |
| 02 | `noun__uncommon.png` | `templates/example_cards/002-covenant/meta.yml` · `5b7da12a22f38e5ea5af0575e6e583e4a922f7c3` | `templates/example_cards/002-covenant/outputs/card_1024x1536.png` · `64ce0912d1e8be999b9461cee68d5702735af516` |
| 03 | `noun__rare.png` | `templates/example_cards/003-wisdom/meta.yml` · `cb6e70c368234f3d611478a60bf7c3e30f19ba16` | `templates/example_cards/003-wisdom/outputs/card_1024x1536.png` · `102a8c303b27b30a2f7f7d2b900ac28f8ed5e6f2` |
| 04 | `noun__glorious.png` | `templates/example_cards/004-glory/meta.yml` · `ce9f877b7b2e323446c1518deef612e1c9ea287e` | `templates/example_cards/004-glory/outputs/card_1024x1536.png` · `48cc4e29f0140bad8cfb2546f2bfd8e4e27e0d39` |
| 05 | `verb__common.png` | `templates/example_cards/005-redeem/meta.yml` · `1a2dd5815536f28be0f94b18682593d622a1cf6d` | `templates/example_cards/005-redeem/outputs/card_1024x1536.png` · `636823d0b3e401d5e631b6997379759f2e0d8c94` |
| 06 | `verb__uncommon.png` | `templates/example_cards/006-forgive/meta.yml` · `08cb780fbca021aac606a6ea802ba0f34388e3c9` | `templates/example_cards/006-forgive/outputs/card_1024x1536.png` · `55afc3f438c63dd9ea5f4bd4c3aab51bcc73d505` |
| 07 | `verb__rare.png` | `templates/example_cards/007-sanctify/meta.yml` · `ca0e22bebfe331c6188e663b5931e983a945811f` | `templates/example_cards/007-sanctify/outputs/card_1024x1536.png` · `d861d4759cd561fa603bc8b14d00e409517c1c95` |
| 08 | `verb__glorious.png` | `templates/example_cards/008-bless/meta.yml` · `93d87602d0d5429912ce00eaa6cdd6f3d7a1d28c` | `templates/example_cards/008-bless/outputs/card_1024x1536.png` · `9fb6be8767d8c7bc3dbf98930cedb085fa16f8f3` |
| 09 | `adjective__common.png` | `templates/example_cards/009-holy/meta.yml` · `5e829ad118e28c02cf87df10a81f011e00f41fa6` | `templates/example_cards/009-holy/outputs/card_1024x1536.png` · `ed50eebbf1ba9f7a28a1cbceabe0709b3582c1a9` |
| 10 | `adjective__uncommon.png` | `templates/example_cards/010-righteous/meta.yml` · `25d56ac72b69b3dd7e9f158591d085d97db6faf9` | `templates/example_cards/010-righteous/outputs/card_1024x1536.png` · `b7f2321106fe7e51593179e5ec6012ac417357d7` |
| 11 | `adjective__rare.png` | `templates/example_cards/011-eternal/meta.yml` · `9bb11d476186cd4d02b7db42e342631e16b354f4` | `templates/example_cards/011-eternal/outputs/card_1024x1536.png` · `413b468d05ec9a4cda9b8740e4e43c28f4cf8cea` |
| 12 | `adjective__glorious.png` | `templates/example_cards/012-sacred/meta.yml` · `56a8199407cb5b06465563b8701eea32acfc4263` | `templates/example_cards/012-sacred/outputs/card_1024x1536.png` · `6db508bb42655b19ba415c57e944f99e25dcbf42` |
| 13 | `name__common.png` | `templates/example_cards/013-moses/meta.yml` · `9973d3f6426788fb56734bde257a009264329b8e` | `templates/example_cards/013-moses/outputs/card_1024x1536.png` · `86bfb4250f11ef69be0a621685e35c5d891e0642` |
| 14 | `name__uncommon.png` | `templates/example_cards/014-david/meta.yml` · `41b48a3e08d983606a186738495c2f4a440958ef` | `templates/example_cards/014-david/outputs/card_1024x1536.png` · `5cc5fb6bd136b1cf30c807bad155463ac6bada96` |
| 15 | `name__rare.png` | `templates/example_cards/015-elijah/meta.yml` · `d83ee38469f7a7325b1d7f4571f7c9464290397c` | `templates/example_cards/015-elijah/outputs/card_1024x1536.png` · `6836c5dadb89c586e1e3036184b698c936077dc1` |
| 16 | `name__glorious.png` | `templates/example_cards/016-abraham/meta.yml` · `10ed5b0402d4d4fd16872bb6f882b521aa26821f` | `templates/example_cards/016-abraham/outputs/card_1024x1536.png` · `7cc3c1071579e1ca9c870b0ff72d5a8503569060` |
| 17 | `title__common.png` | `templates/example_cards/017-shepherd/meta.yml` · `5d9365f5ad2bb944af119ad2b76d457c45c4004f` | `templates/example_cards/017-shepherd/outputs/card_1024x1536.png` · `f46af028886834b13f13af8689a85d6b7648464e` |
| 18 | `title__uncommon.png` | `templates/example_cards/018-redeemer/meta.yml` · `bda3271a728fbefff62ff10eaa0c36768147e06f` | `templates/example_cards/018-redeemer/outputs/card_1024x1536.png` · `ecb50fc3f711926db0ad027cabd61a7d3594e6f3` |
| 19 | `title__rare.png` | `templates/example_cards/019-savior/meta.yml` · `15f17e2e617ceb9e2a31ae7d4befb7f3d3cf82c9` | `templates/example_cards/019-savior/outputs/card_1024x1536.png` · `03f4231e4d13f05bf07be2927417099c00a57f2d` |
| 20 | `title__glorious.png` | `templates/example_cards/020-messiah/meta.yml` · `ea3624d83d6ab5b10bfd54ee83f0964941828e45` | `templates/example_cards/020-messiah/outputs/card_1024x1536.png` · `2d34b03afcaf2dbea1611d3d3257b0e12ee59f31` |

Expected companion outputs:

- `manifest.json`: authority commit; base/type/rarity paths and blob IDs; 20 records with cell number, type, rarity, output filename, witness paths/blobs, output SHA-256, width, height, mode, and format.
- `contact_sheet.png`: five rows in order `noun, verb, adjective, name, title`; four columns in order `common, uncommon, rare, glorious`; labels outside card pixels.
- `checks.json`: every objective check below with pass/fail and measured values.

## Objective acceptance checks

1. **Input identity:** `git rev-parse <authority>:<path>` equals every specified blob ID before construction. Any mismatch is a hard failure.
2. **Cardinality:** exactly 20 card PNGs exist, and the Cartesian key set equals the five type keys × four rarity keys with no missing, duplicate, or extra cell.
3. **Raster contract:** every card decodes as PNG, is exactly 848 × 1264, and is RGB or RGBA. Each output SHA-256 is recorded.
4. **Determinism:** a clean second build from the same blobs produces the same SHA-256 for all 20 card outputs and companion outputs (excluding timestamps; manifests must omit volatile timestamps).
5. **Shared-pixel invariance:** outside the union of the explicitly recorded type mask and rarity mask, every output is pixel-identical to the base. Store both masks or their bounding boxes plus mask SHA-256 in `manifest.json`.
6. **Type isolation:** for a fixed rarity, the four pairwise changes among the five type outputs are confined to the type mask; rarity-mask pixels outside any overlap are identical. Automated image diff must report zero changed pixels outside the type mask.
7. **Rarity isolation:** for a fixed type, changes among the four rarity outputs are confined to the rarity mask; type-mask pixels outside any overlap are identical. Automated image diff must report zero changed pixels outside the rarity mask.
8. **Icon correctness:** each row contains exactly its named white icon centered within the unchanged navy type circle; compare to the named type reference and palette. No substituted or malformed icon passes visual review.
9. **Rarity correctness:** common = white/no cards; uncommon = green `#2E8B57`/no cards; rare = gold `#C9A44C`/one card; glorious = orange `#F28C28`/two cards. Count the card ornaments explicitly; verify diamond colors at the solid interior sample points recorded in `checks.json`.
10. **Border registration:** compare each output to base along the full outer frame and gold inset. Common and uncommon must have zero changed pixels there. Rare/glorious may differ only where the predeclared rarity mask intersects the restrained accent; all four edge locations and all four corners remain registered with zero displacement.
11. **Geometry registration:** fixed landmark bounding boxes (type pill/circle, rarity tab, title, definition, art frame, stat row, each panel, trivia, footer) are copied once from base into `manifest.json`; every output must match those boxes exactly with 0 px translation and 0 px size delta.
12. **Witness sanity:** each metadata witness declares the matrix type/rarity assigned to its cell. Witness images guide symbol identity only; differences in border thickness/hue/glow, typography, panel positions, or encoding are explicitly rejected as drift.
13. **Canonical immutability:** before/after blob IDs for all 12 canonical inputs (base + five type + four rarity + two palettes) are identical, and `git diff -- templates/` is empty.

A build is accepted only when all 13 checks pass. A failed identity, cardinality, isolation, geometry, or immutability check invalidates the entire matrix rather than only one cell.

