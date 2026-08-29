"""Repair CREATION's TITLE icon by SHOWING the model the right glyph.

Earlier attempts described the glyph in words ("light outline picture frame") and
measured the result with fill ratios and IoU - none of which capture 'ornate scrolled
frame' vs 'plain rectangle'. The card pipeline's answer to this is style references:
put the correct artifact in front of the model as an image and tell it to copy.

Image 1 is the card being corrected (fix mode). Images 2-3 are lots whose TITLE glyph
is correct, one of them the same 7-slot layout so the scale matches.
"""
import sys, shutil
from pathlib import Path
import yaml
sys.path.insert(0, "scripts/pipeline")
from lot_gates import icon_fills
from hypertext.lots.rules import load_lot_rules
from hypertext.lots.renderer import render_lot_card

SERIES=Path("series/2026-Q1"); FACES=SERIES/"lots"/"faces"; DEV=Path("series/2026-Q1-dev/lots")
SCRATCH=Path("/tmp/claude-1000/-home-cap-Code-Hypertext/51dcdd88-c49d-4b61-a082-0bfa42d56523/scratchpad/lotfix")

CORRECTION = (
 "FIX MODE. Image 1 is the card to correct. Images 2 and 3 are Lot cards from this same "
 "set whose card-type icons are CORRECT - image 2 has the identical 7-slot layout.\n\n"
 "ONE change: redraw the icon above the TITLE label so it is the SAME ornate picture-frame "
 "glyph used in images 2 and 3 - a decorated frame with scrolled, carved ornament on its top "
 "and bottom edges and thick moulded sides, drawn in the same dark navy line weight as the "
 "NOUN book and NAME quill icons already on image 1. It must NOT be a plain thin rectangle "
 "and must NOT be a solid filled block. Copy the frame from images 2 and 3 exactly.\n\n"
 "Everything else must be identical to image 1, pixel for pixel: the title CREATION, the "
 "flavor line, CHAPTER VALUE: 14 POINTS, PORTION VALUE: 2/3 LETTERS, the Genesis 1:1 verse "
 "line, the NOUN VERB ADJECTIVE NAME TITLE labels and the PAIR bracket, the CONTEXT "
 "paragraph, the footer and the border. Add, remove and reword nothing."
)

def main(attempts=3):
    rules={r["id"]:r for r in load_lot_rules()}
    r=rules[27]; slug="27-creation"
    meta=yaml.safe_load((DEV/slug/"meta.yml").read_text(encoding="utf-8"))
    data=dict(r); data.update({"flavor":meta["flavor"],"context":meta["context"],
                               "series":"2026-Q1","theme":"Babel","revision":CORRECTION})
    refs=[str(FACES/"27-creation.png"),          # image 1: the card being fixed
          str(FACES/"28-revelation.png"),        # image 2: same 7-slot layout, correct TITLE
          str(FACES/"02-pentateuch.png")]        # image 3: the cleanest icon set
    print("style refs:", [Path(p).name for p in refs])
    outs=[]
    for a in range(1, attempts+1):
        out=SCRATCH/f"creation-sr{a}.png"
        render_lot_card(data, out, style_refs=refs)
        print(f"  a{a} fills {[round(v,3) for v in icon_fills(out, r['composition'])]}")
        outs.append(out)
    return outs

if __name__=="__main__":
    main()
