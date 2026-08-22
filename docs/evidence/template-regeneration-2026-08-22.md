# Face-template regeneration evidence — 2026-08-22

Model: `gemini-3.1-flash-image`. Request settings: Gemini style-reference generation, portrait `2:3` at Gemini `2K`, normalized by the repository image contract to truthful RGB PNG at `1024x1536`. All references were canonical face templates or the type/rarity palettes; no card back was used. Scheduled automation remained disabled.

| Template | Attempts | Automated contract | Visual result |
|---|---:|---|---|
| card/base | 2 | pass | accepted |
| card/common | 1 | pass | accepted |
| card/uncommon | 2 | pass | accepted |
| card/rare | 2 | pass | accepted |
| card/glorious | 2 | pass | accepted |
| card/noun | 2 | pass | accepted |
| card/verb | 2 | pass | accepted |
| card/adjective | 2 | pass | accepted |
| card/name | 2 | pass | accepted |
| card/title | 2 | pass | accepted |
| lot/base | 2 | pass | accepted |
| lot/5-card | 1 | pass | accepted: 8 Points / 2 Letters |
| lot/6-card | 1 | pass | accepted: CONGREGATION, 10 Points / 2 Letters |
| lot/7-card | 1 | pass | accepted: 14 Points / 3 Letters |

Canonical assets are saved as `templates/card/v001/{base,common,uncommon,rare,glorious,noun,verb,adjective,name,title}/template_1024x1536.png` and `templates/lot/v001/{base,5-card,6-card,7-card}/template_1024x1536.png`. Each adjacent `generation.json` records the final API response metadata, model, latency, reference count, dimensions, MIME type, and token usage. Every output was opened and inspected at full-card scale after generation; targeted second attempts corrected the observed subtype or visible-copy drift. No template remained unaccepted.
