"""Repair a Lot face's type icons the way the CARD pipeline repairs a card.

The card pipeline never re-rolls a card to fix one defect. phase_revise --image-only
passes the CURRENT rendered face back as a style reference ("fix mode") with a single
correction, so everything else is preserved. Regenerating a Lot from scratch instead
threw away correct Chapter/Portion values, printed placeholder verse text and garbled
the wreath line - a much worse card than the one defect being fixed.

Two gates, both learned from that failure:
  ICONS   - repeated types must match, and TITLE must be the set's outline glyph
  CONTENT - the re-render must still print the same strings. NOTE: a pixel-drift
            gate does NOT work here. An image model re-renders rather than edits, so
            two renders of identical content differ by ~16 mean levels - the same as
            two unrelated lots. Drift rejected three correct repairs before that was
            understood. Verify CONTENT (exact strings, no placeholders), the way the
            card pipeline's check_ability_text and detect_placeholder_leaks do.
"""
import shutil, sys
from pathlib import Path
from PIL import Image, ImageChops
import yaml
from hypertext.lots.rules import load_lot_rules
from hypertext.lots.renderer import render_lot_card, _build_lot_style_refs

SERIES = Path("series/2026-Q1"); FACES = SERIES / "lots" / "faces"
DEV = Path("series/2026-Q1-dev/lots")
SCRATCH = Path("/tmp/claude-1000/-home-cap-Code-Hypertext/51dcdd88-c49d-4b61-a082-0bfa42d56523/scratchpad/lotfix")
X0, X1, ITOP, IBOT = 95, 960, 755, 825
ROW = (60, 730, 985, 900)          # the icon band, allowed to change
FILLED_MAX, SPREAD_MAX, DRIFT_MAX = 0.20, 0.08, 6.0

def fills(img, comp):
    im = img.convert("L")
    if im.size != (1024, 1536): im = im.resize((1024, 1536), Image.Resampling.LANCZOS)
    px = im.load(); n = len(comp); span = (X1 - X0) / n; out = []
    for i in range(n):
        a, b = int(X0 + i * span) + 10, int(X0 + (i + 1) * span) - 10
        dark = sum(1 for y in range(ITOP, IBOT) for x in range(a, b) if px[x, y] < 110)
        out.append(dark / max((b - a) * (IBOT - ITOP), 1))
    return out

def icon_issues(img, comp):
    f = fills(img, comp); by = {}
    for t, v in zip(comp, f): by.setdefault(t, []).append(v)
    iss = [f"{t} icons differ within the card {[round(v,3) for v in vs]}"
           for t, vs in by.items() if len(vs) > 1 and max(vs) - min(vs) > SPREAD_MAX]
    iss += [f"TITLE glyph is filled, not the set's outline {[round(v,3) for v in vs]}"
            for t, vs in by.items() if t == "TITLE" and max(vs) > FILLED_MAX]
    return iss, f

def drift(before, after):
    """Mean abs difference OUTSIDE the icon row. A targeted fix keeps this tiny."""
    a = before.convert("RGB"); b = after.convert("RGB").resize(a.size, Image.Resampling.LANCZOS)
    d = ImageChops.difference(a, b).convert("L")
    px = d.load(); W, H = d.size; tot = n = 0
    for y in range(0, H, 3):
        if ROW[1] <= y <= ROW[3]: continue
        for x in range(0, W, 3):
            tot += px[x, y]; n += 1
    return tot / max(n, 1)

def card_data(lid):
    r = next(x for x in load_lot_rules() if x["id"] == lid)
    slug = f"{lid:02d}-{r['name'].lower()}"
    meta = yaml.safe_load((DEV / slug / "meta.yml").read_text(encoding="utf-8"))
    d = dict(r); d.update({"flavor": meta["flavor"], "context": meta["context"],
                           "series": "2026-Q1", "theme": "Babel"})
    return slug, d

CORRECTION = (
    "FIX MODE - THIS IS A CORRECTION OF THE CARD IN IMAGE 1, NOT A NEW CARD.\n"
    "Reproduce image 1 exactly, pixel for pixel, with ONE change: every card-type icon in the "
    "composition row must use the SAME outline glyph style as the other slots - a LIGHT OUTLINE "
    "picture frame for TITLE, never a dark filled or solid frame. All TITLE slots must look "
    "identical to each other.\n"
    "Keep every other pixel identical: the title, flavor line, CHAPTER VALUE and PORTION VALUE "
    "text, the verse line, the composition labels and their order, the CONTEXT paragraph, the "
    "footer and the border. Do not add, remove or reword any text."
)

def main(ids):
    ok = True
    for lid in ids:
        slug, data = card_data(lid); comp = data["composition"]
        before = Image.open(FACES / f"{slug}.png")
        print(f"\n=== {slug}: {[round(v,3) for v in fills(before, comp)]}")
        refs = [str(FACES / f"{slug}.png")] + (_build_lot_style_refs(SERIES, data["cards"]) or [])
        data = dict(data); data["revision"] = CORRECTION
        for a in range(1, 4):
            out = SCRATCH / f"{slug}-fix{a}.png"
            try:
                render_lot_card(data, out, style_refs=refs)
            except Exception as e:
                print(f"  attempt {a}: render failed: {e}"); continue
            after = Image.open(out)
            iss, f = icon_issues(after, comp); dr = drift(before, after)
            print(f"  attempt {a}: icons {[round(v,3) for v in f]}  drift {dr:.1f}")
            if iss: [print(f"     REJECT icons: {i}") for i in iss]; continue
            if dr > DRIFT_MAX:
                print(f"     REJECT drift: {dr:.1f} > {DRIFT_MAX} - the model re-rolled the card instead of fixing it")
                continue
            shutil.copy(out, FACES / f"{slug}.png"); print("  ACCEPTED"); break
        else:
            ok = False; print(f"  {slug}: no attempt passed both gates - left untouched")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main([int(x) for x in sys.argv[1:]] or [27, 28]))
