# End-to-end quality evidence packet

Date: 2026-08-22. No API calls were made for this packet. The representative
inputs are the four existing cards in `/home/cap/random-card-run-2026-08-21-v4`.
Their card JSON, prompt, ordered-reference log, generation record, PNG, and two-stage
grade were inspected as the reusable baseline described in the evaluation document.

| Boundary | Before (existing v4 artifacts/code) | After (offline contract) |
|---|---|---|
| Plan | Card facts existed, but no stage digest or bounded field contract. | Required identity/art/stat fields and 0–5 integer pips are validated; inputs and outputs can be SHA-256 attributed. |
| Prompt | Full-card prompts let the model own text and geometry. | `assemble_art_prompt` explicitly requests illustration only and forbids words, numbers, UI, pips, badges, frames, and watermarks. |
| References | Paths and rarity labels were logged, but quality was not an eligibility rule. | Stable ranking admits only references that cleared 100/100 and records the selection reason. |
| Request/candidates | Stable model request validation existed, but consumers effectively accepted the first image. | Candidate selection requires successful image bytes, rejects timeout/no-output, maximizes contract score, and breaks ties by original order. |
| Composite/revision | Pips were repaired deterministically; other revision paths could ask the image model to repair owned text. | Only dimension/format/pip/metadata deterministic repairs are eligible; model text repair is rejected. |
| Review | Some execution paths returned success at 90/100. Categories did not match the captured requirement. | Composition, typography, template fidelity, metadata, stat pips, and artifact cleanliness each score 0–100; the minimum is authoritative and every axis must be 100. |

The existing v4 cards remain historical evidence rather than being relabeled by the
new contract. This is deliberately a before/contract-after packet: generating new
art would add cost without proving deterministic boundary behavior. Regression tests
exercise the after behavior, including timeout failure, stable ties, invalid pips,
non-deterministic repair rejection, bounded attempts, and the exact rollout gate.

