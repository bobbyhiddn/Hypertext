# Rejected operator review: visual defect matrix

The 2026-08-22 package is failed visual QA. PNG validity did not constitute acceptance.

| Defect | Affected assets | Evidence |
|---|---|---|
| Cross-family and subtype geometry drift | all 14 templates; all 7 cards | Header, title, art, facts, composition, context, and footer coordinates visibly change instead of using family grids. |
| Header/type/rarity contract conflicts | card base, common, uncommon, rare, glorious, noun, verb, adjective, name, title; four generated Cards | Badges alternate between tabs, circles, pills, detached diamonds, and text-only rarity; labels and icon scales are inconsistent. |
| Typography hierarchy and exact-label drift | all Card templates; all generated Cards; Lot base | Mixed font families/cases/sizes; `TYPE NAME`, `Rarity (no icons)`, `Collector ID`, `CARD TITLE`/`Title`; microtype is compressed and some generated copy is not reliably sharp. |
| Facts/panel hierarchy drift | all Card templates; four generated Cards | Ability/verse/language/trivia bars use incompatible heights, borders, alignment, and fills; noun and verb are a different grid family. |
| Palette/frame language drift | noun, verb, all Lots, generated Cards | White/gold art fill, heavy navy rounded frame, thin square frame, and ornate Lot frames do not share rule weights, margins, corner radii, or parchment treatment. |
| Iconography drift | all type templates; all Lots; generated Cards | Book, pencil, sparkle, quill, crown, feather and composition icons vary in silhouette, container, stroke, size, and sometimes meaning. |
| Lot subtype/size distinction errors | Lot base, 5-card, 6-card, 7-card; all generated Lots | Composition frame and context ornament change with size; generated `SCROLL` begins with NAME while its saved contract expects the canonical size composition; 6-card uses `[MATCH]` repetition instead of type slots. |
| Content placement and duplication risk | all generated Cards and Lots | Long definitions, verses, scripts, trivia, and context are model-drawn into undersized zones; inconsistent wrapping crowds borders and defeats deterministic full-card ownership. |
| Blur/halos and legibility | all generated Cards; Lot context microtype | Resampled/model-rendered small text and icon edges show softness; bright art contains glow/halo that approaches frame/text zones. |
| Crop/safe-zone inconsistency | noun, verb, Lot family | Outer frame inset, header tangencies, and footer baselines differ; some elements sit too near trim/safe boundaries. |
| Generation drift | all 14 regenerated templates and seven-card package | Each subtype used its own rejected image as a leading reference, recursively preserving a separate visual dialect. |
