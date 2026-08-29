import shutil, sys, yaml
from pathlib import Path
sys.path.insert(0, "scripts/pipeline")
from lot_gates import check_icons, check_content, icon_fills
from hypertext.lots.rules import load_lot_rules
from hypertext.lots.renderer import render_lot_card, _build_lot_style_refs

SERIES=Path("series/2026-Q1"); FACES=SERIES/"lots"/"faces"; DEV=Path("series/2026-Q1-dev/lots")
SCRATCH=Path("/tmp/claude-1000/-home-cap-Code-Hypertext/51dcdd88-c49d-4b61-a082-0bfa42d56523/scratchpad/lotfix")
CORRECTION=("FIX MODE - correct the card in image 1, do not invent a new card.\n"
 "ONE change: draw every card-type icon in the composition row in the SAME weight and style as the "
 "other slots on this card and on the reference cards - a medium-weight LIGHT OUTLINE picture frame "
 "for TITLE, clearly drawn, neither a dark solid frame nor a faint hairline. Every TITLE slot must "
 "look identical.\nKeep every other pixel identical: title, flavor line, CHAPTER VALUE and PORTION "
 "VALUE text, the verse line, the composition labels and their order, the CONTEXT paragraph, the "
 "footer and the border. Do not add, remove or reword any text.")

def main(ids, attempts=4):
    rules={r["id"]:r for r in load_lot_rules()}; ok=True
    for lid in ids:
        r=rules[lid]; slug=f"{lid:02d}-{r['name'].lower()}"
        meta=yaml.safe_load((DEV/slug/"meta.yml").read_text(encoding="utf-8"))
        # The dev meta is NOT the source of truth for the published faces - CREATION's
        # flavor differs - so read the printed line off the face being repaired.
        from hypertext.gemini.review import _call_gemini, _parse_json_response
        pub=_parse_json_response(_call_gemini(
            'Transcribe EXACTLY, no correction. Return ONLY JSON: '
            '{"flavor":"<the italic line directly under the big title>",'
            '"context":"<the CONTEXT paragraph>"}', image_path=FACES/f"{slug}.png"))
        meta={"flavor": pub.get("flavor") or meta["flavor"],
              "context": pub.get("context") or meta["context"]}
        print(f"  published flavor: {meta['flavor']!r}")
        data=dict(r); data.update({"flavor":meta["flavor"],"context":meta["context"],
                                   "series":"2026-Q1","theme":"Babel","revision":CORRECTION})
        refs=[str(FACES/f"{slug}.png")]+(_build_lot_style_refs(SERIES,r["cards"]) or [])
        print(f"\n=== {slug}  current {[round(v,3) for v in icon_fills(FACES/f'{slug}.png', r['composition'])]}")
        for a in range(1,attempts+1):
            out=SCRATCH/f"{slug}-r{a}.png"
            try: render_lot_card(data,out,style_refs=refs)
            except Exception as e: print(f"  a{a}: render failed {e}"); continue
            ii=check_icons(out,r["composition"])
            print(f"  a{a}: {[round(v,3) for v in icon_fills(out,r['composition'])]}")
            if ii: [print(f"     REJECT {x}") for x in ii]; continue
            ci=check_content(out,r,meta["flavor"])
            if ci: [print(f"     REJECT content: {x}") for x in ci]; continue
            shutil.copy(out,FACES/f"{slug}.png"); print("  ACCEPTED (icons + content)"); break
        else: ok=False; print(f"  {slug}: no attempt passed")
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main([int(x) for x in sys.argv[1:]]))
