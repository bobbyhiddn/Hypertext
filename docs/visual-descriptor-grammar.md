# Visual descriptor grammar (foundation)

This offline foundation traces REQ-PPAUG-016 through REQ-PPAUG-022. The machine-readable hierarchy is `schema/hypertext_visual_descriptors.json`; its schema is `schema/visual_descriptor.schema.json`. One global descriptor and one Word Card structure inherit five isolated type treatments and four isolated rarity treatments to form 20 logical combinations without authoring 20 whole-card prompt templates. Three LOT size descriptors cover the existing five-, six-, and seven-card families; all inherit the canonical global canvas.

`serialize_word_card_prompt` supports the declared `EXPLICIT` and `PATTERN` composition modes. Both serialize canonical content as Unicode JSON, enforce the canonical 1024×1536 canvas and invariant geometry, repeat Old Testament/Hebrew-Aramaic-left and New Testament/Greek-right placement, and append the complete checked-in negative grammar including the prohibition on a generated watermark. The module is deliberately not wired to an automated generation command; existing generation remains manual-only.

## Supplied-specification boundary

The received Lot Reward section ended after the word `trim`. Accordingly, the LOT descriptor represents only the already declared title/art/reward ordering and vertical navy-border/gold-trim frame geometry. It does not infer reward copy, typography, color, placement, or further geometry. Exact pixel coordinates beyond the canonical canvas and the existing Word Card art-panel fraction were not recoverable from the supplied repository contracts, so they remain a specification gap rather than invented values.
