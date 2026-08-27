# Hypertext Roadmap

## 1. Complete Rarity Reference Set

**Priority:** High  
**Status:** ✅ Complete

Ensure the style reference set includes at least one card of each rarity tier:
- COMMON (white diamond)
- UNCOMMON (green diamond)
- RARE (gold diamond)
- GLORIOUS (orange diamond)

This ensures the image generation model always has a visual example of the target rarity's badge style, corner treatment, and any rarity-specific visual cues.

**Tasks:**
- [x] Generate/select representative cards for each rarity
- [x] Update `_build_style_refs()` in `daily_pipeline.py` to include rarity-matched references
- [ ] Test generation across all rarity tiers

---

## 2. Series Monitor & Rarity Distribution

**Priority:** High  
**Status:** 🚧 In Progress

Track series progress and maintain target rarity distribution across 90-day cycles.

**Rarity Targets:**
| Rarity | Target % |
|--------|----------|
| GLORIOUS | 10% |
| RARE | 15% |
| UNCOMMON | 35% |
| COMMON | 40% |

**Current State (2026-Q1):**
- 5 cards created
- Series cycle: 90 days
- Ratios reset at start of each new series

**Requirements:**
- Track card count per series
- Track rarity distribution vs targets
- Queue generation aware of what rarities are needed
- Auto-balance: prioritize under-represented rarities
- Series metadata file with start date, target count, current stats

**Technical Approach:**
- `series/<SERIES>/stats.yml` - tracks counts and distribution
- Update `_generate_queue_entries()` to check stats and bias toward needed rarities
- Add `--series-stats` flag to daily pipeline for reporting

**Tasks:**
- [x] Create `series/2026-Q1/stats.yml` with current counts
- [x] Implement rarity tracking in pipeline
- [x] Update queue generation to respect distribution targets
- [x] Rarity-aware style reference labeling (highlights matching rarity)
- [ ] Add series progress reporting
- [ ] Document 90-day cycle process

---

## 3. Dynamic Reference Weighting

**Priority:** Medium  
**Status:** Planned (prerequisite: one card per suit per rarity)

Improve style reference selection by matching suit AND rarity when sufficient cards exist.

**Current State:**
- References: 1 template + 1 card per rarity (up to 5 total)
- Highlights matching rarity in prompt

**Future State (once set is complete):**
- References matched by both suit (NOUN/VERB/ADJECTIVE/NAME/TITLE) and rarity
- Max 16 references supported by Gemini API
- Could pass: template + same-suit examples + same-rarity examples

**Phases:**
1. **Phase 1** (current): One card per rarity as reference
2. **Phase 2**: Add suit-matching when 1+ card per suit exists
3. **Phase 3**: Full matrix - prioritize same-suit-same-rarity, then same-rarity, then same-suit

**Technical Approach:**
- Extend `_find_card_by_rarity()` to also index by suit (card_type)
- Update `_build_style_refs()` to accept target suit + rarity
- Weight prompt labels: `⭐⭐ PRIMARY (same suit + rarity)` vs `⭐ (same rarity only)`

**Tasks:**
- [ ] Wait for at least one card per suit (5 types)
- [ ] Extend card indexing to track suit + rarity
- [ ] Implement suit-aware reference selection
- [ ] Update prompt labeling for multi-dimension matching
- [ ] Test with full reference set

---

## 4. GitHub Pages Deck Gallery

**Priority:** Medium  
**Status:** ✅ Complete

Build a static site (GitHub Pages) that displays card decks by series, updated automatically when new cards are created.

**Requirements:**
- Display cards grouped by series (e.g., 2026-Q1)
- Cards listed in numerical order by default
- Sortable/filterable by rarity
- Clean, modern UI (responsive, card grid layout)
- Auto-updated via GitHub Actions after daily pipeline completes

**Technical Approach:**
- Static site generator (custom script `tools/build_gallery.py`)
- Card metadata from `meta.yml` files
- Card images from `outputs/card_1024x1536.png`
- Workflow `deploy-gallery.yml` builds and deploys to `github-pages` environment

**Tasks:**
- [x] Design gallery layout and card display
- [x] Create static site scaffold in `/docs` or `/site`
- [x] Write build script to aggregate card data
- [x] Add GitHub Actions step to deploy to Pages
- [x] Implement rarity sorting/filtering

---

## 5. Cryptographic Card Watermark

**Priority:** Medium  
**Status:** Planned

Implement a tamper-evident watermark system using a repository secret to authenticate cards.

**Requirements:**
- Small SVG watermark in bottom-right corner of each card
- Watermark encodes: card data hash + signature derived from repo secret
- SVG stored in card folder alongside the image
- Cannot be reproduced without the secret
- Verifiable: given card data + watermark, can confirm authenticity

**Technical Approach:**
- Use HMAC-SHA256 with repo secret as key
- Input: canonical card JSON (word, number, series, etc.)
- Output: truncated hash encoded as visual pattern or QR-like micro-glyph
- SVG overlaid on card PNG during post-processing

**Tasks:**
- [ ] Design watermark visual format (micro-glyph, data matrix, etc.)
- [ ] Implement `tools/watermark.py` for generation
- [ ] Add `HYPERTEXT_SIGNING_KEY` to GitHub secrets
- [ ] Integrate into daily pipeline post-image-gen
- [ ] Create verification script
- [ ] Regenerate cards 001-004 with watermarks

---

## Completed

- ✅ Multi-reference style generation
- ✅ Extended queue format (full card specs)
- ✅ Review pipeline with Gemini 3 SDK
- ✅ Prompt conflict fix for style references
- ✅ Targeted card revision tool
