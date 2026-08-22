# Deterministic reconstruction validation

- Scope: 20 canonical word templates, all 31 canonical Babel cards rendered through those templates, and 3 shared Lot size subtypes.
- Composition: frozen approved base plus disjoint bounded type and rarity rectangles; no model or image API used.
- Mechanical validation: all outputs are PNG, 1024×1536, matrix-exact, reproducible, and represented by SHA-256 in their manifests. The canonical render manifest maps each of the 31 source records to its exact type/rarity template.
- Visual inspection: frame, panel geometry, safe areas, and ornaments remain aligned across the word matrix. Lot geometry remains aligned across the shared family. The grouped canonical-card contact sheet is ordered by type, rarity, then collector number.
- Resolved source-limited labels: bounded deterministic overlays replace `TYPE PILL`/`TYPE NOUN`-style copy with the authoritative `NOUN`, `VERB`, `ADJECTIVE`, `NAME`, or `TITLE` identity, and replace generic `Rarity` copy with the authoritative `COMMON`, `UNCOMMON`, `RARE`, or `GLORIOUS` tier.
- Resolved Lot values: every shared size now spells out `CHAPTER: N POINTS` and `PAGE: N LETTERS` in the existing reward ribbon, using the values in `schema/lot_template_family.json` and `templates/phases.yml`.
- Wording authority finding: `CONGREGATION` is not a defect. `templates/phases.yml` defines it as Lot 15, the six-card `6 any mix` phase; `ASSEMBLY` is a separate six-card `3 + 3 (two types)` phase. The 6-card source title remains `CONGREGATION` to avoid inventing or conflating canonical terms.
- Unresolved authority gaps: none for the four reported items. No model or image API was used.
