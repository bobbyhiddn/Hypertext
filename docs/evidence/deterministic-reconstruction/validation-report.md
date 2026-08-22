# Deterministic reconstruction validation

- Scope: 20 canonical word templates and 3 shared Lot size subtypes.
- Composition: frozen approved base plus disjoint bounded type and rarity rectangles; no model or image API used.
- Mechanical validation: all outputs are PNG, 1024×1536, matrix-exact, reproducible, and represented by SHA-256 in their manifests.
- Visual inspection: frame, panel geometry, safe areas, and ornaments remain aligned across the word matrix. Lot geometry remains aligned across the shared family.
- Source-limited defects: approved UNCOMMON, RARE, and GLORIOUS rarity sources retain the generic `Rarity` placeholder rather than distinct visible tier labels. Several approved type sources retain placeholder-like pill copy, and the 6-card Lot source uniquely says `CONGREGATION`. Shared Lot reward banners expose both numeric values but use the compact `REWARD: points / letters` presentation rather than spelling out Chapter/Page roles. No new semantic captions or invented ornament were added to conceal these upstream defects.
