#!/usr/bin/env python3
"""Repair two label defects in the composed Word-Card template package.

Found 2026-08-28 while stamping fixed elements deterministically:

1. Every UNCOMMON composed template sets "Uncommon" too wide for the rarity
   block, so the "U" is clipped by the block's left edge.  The image model had
   been hiding this by painting its own wider chip; the deterministic stamp
   copies the template faithfully and exposed it.
2. Every TITLE composed template carries the NOUN type pill, because the
   historical TITLE witness was a NOUN card.

Both defects live in pixels that are identical across the affected templates
(the five UNCOMMON chips are pixel-identical, as are the four TITLE pills), so
each repair is one RGB patch.  The patches are built here from the templates
themselves plus text set in Liberation Serif (fonts pinned by SHA-256), written
to templates/card/v001/composed/repair/, and declared in the composed manifest
so that reconstruction stays a pure pixel paste:

  * TITLE outputs point their `type_label_source` at a repaired witness whose
    pill reads TITLE; the existing `paste_type_label_crop` stage does the rest.
  * A new `uncommon_rarity_word_repair` stage pastes the word patch on every
    UNCOMMON output.

`--preview DIR` writes close-ups without touching the package.  `--apply`
rewrites the eight PNGs, both manifests, and prints the new pins for
tools/verify_template_package.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import PIL
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "templates" / "card" / "v001" / "composed"
MANIFEST = PACKAGE / "manifest.json"
PERSISTENCE = PACKAGE / "persistence-manifest.json"
REPAIR_DIR = PACKAGE / "repair"
CONTRACT = "hypertext.template-label-repair/v1"
TODAY = date(2026, 8, 28).isoformat()

# --- rarity word (native 848x1264 canvas coordinates) ---------------------
WORD_BOX = (652, 13, 791, 56)          # block left edge through the word/diamond gap
WORD_CLEAR = (664, 27, 791, 51)        # rows/cols the clipped word occupies, incl. fringe
WORD_EDGE_COLS = (658, 664)            # inner-edge columns the old "U" overlapped; taken from the COMMON block over the cleared rows only
WORD_PROFILE_COLS = (700, 781)         # glyph-free interior columns used for the row profile
WORD_TEXT = "Uncommon"
WORD_RIGHT = 786                       # every rarity word ends here, 9px short of the diamond
WORD_CAP_TOP, WORD_BASELINE = 29, 48   # "Common" cap rows on the same templates
WORD_FONT_SIZE = 29                    # cap height 19 in Liberation Serif Regular
WORD_CONDENSE = 0.87                   # keeps a 9px inset from the block edge
WORD_COLOUR = (141, 140, 151)          # median of the template's own "Uncommon" glyph pixels
# --- type pill --------------------------------------------------------------
PILL_BOX = (122, 24, 274, 58)          # manifest type_label_box
PILL_INTERIOR = (126, 28, 214, 54)     # inside the pill's light outline
PILL_RADIUS = 13
PILL_FILL = (7, 6, 22)                 # median of the pill navy on the TITLE templates
PILL_TEXT = "TITLE"
PILL_CENTER_X = 168.5                  # NOUN glyphs span 133..204
PILL_CAP_TOP, PILL_BASELINE = 32, 49
PILL_FONT_SIZE = 26                    # cap height 17 in Liberation Serif Bold
PILL_CONDENSE = 0.92
PILL_COLOUR = (235, 234, 247)          # median of the NOUN glyph pixels
SUPERSAMPLE = 4
GLYPH_SOFTEN = 0.4                     # matches the templates' softly upscaled glyph edges

TYPE_ORDER = ("NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE")
RARITY_ORDER = ("COMMON", "UNCOMMON", "RARE", "GLORIOUS")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font_file(family: str) -> Path:
    out = subprocess.run(["fc-match", "-f", "%{file}", family], capture_output=True, text=True, check=True).stdout.strip()
    path = Path(out)
    if not path.is_file():
        raise SystemExit(f"font not found for {family!r}: {out}")
    return path


def render_word(text: str, font_path: Path, size: int, condense: float, cap_height: int, colour: tuple[int, int, int]) -> Image.Image:
    """Set `text` at `size`, condensed horizontally, scaled so the glyph box is
    exactly `cap_height` rows tall.  Returns an RGBA layer cropped to the glyphs."""
    font = ImageFont.truetype(str(font_path), size * SUPERSAMPLE)
    bbox = font.getbbox(text)
    big = Image.new("L", (bbox[2] - bbox[0] + 8, bbox[3] - bbox[1] + 8), 0)
    ImageDraw.Draw(big).text((4 - bbox[0], 4 - bbox[1]), text, font=font, fill=255)
    big = big.crop(big.getbbox())
    width = max(1, round(big.width / SUPERSAMPLE * condense))
    alpha = big.resize((width, cap_height), Image.Resampling.LANCZOS)
    if GLYPH_SOFTEN:
        alpha = alpha.filter(ImageFilter.GaussianBlur(GLYPH_SOFTEN))
    layer = Image.new("RGBA", alpha.size, colour + (0,))
    layer.putalpha(alpha)
    return layer


def median_rgb(points: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    return tuple(sorted(p[i] for p in points)[len(points) // 2] for i in range(3))


def build_word_patch(template: Image.Image, common: Image.Image, regular: Path) -> Image.Image:
    """The rarity-word patch: the UNCOMMON block with its clipped word cleared to
    the block's own row profile, the inner edge the old "U" overlapped restored
    from the COMMON block (identical construction, clean edge), and "Uncommon"
    re-set to fit."""
    patch = template.crop(WORD_BOX)
    ox, oy = WORD_BOX[:2]
    edge = common.crop((WORD_EDGE_COLS[0], WORD_CLEAR[1], WORD_EDGE_COLS[1], WORD_CLEAR[3]))
    patch.paste(edge, (WORD_EDGE_COLS[0] - ox, WORD_CLEAR[1] - oy))
    px = patch.load()
    c0, c1 = WORD_PROFILE_COLS[0] - ox, WORD_PROFILE_COLS[1] - ox
    y0, y1 = WORD_CLEAR[1] - oy, WORD_CLEAR[3] - oy
    above = median_rgb([px[x, y0 - 1] for x in range(c0, c1)])
    below = median_rgb([px[x, y1] for x in range(c0, c1)])
    for y in range(y0, y1):
        t = (y - (y0 - 1)) / (y1 - (y0 - 1))
        row = tuple(round(above[i] + (below[i] - above[i]) * t) for i in range(3))
        for x in range(WORD_CLEAR[0] - ox, WORD_CLEAR[2] - ox):
            px[x, y] = row
    layer = render_word(WORD_TEXT, regular, WORD_FONT_SIZE, WORD_CONDENSE, WORD_BASELINE - WORD_CAP_TOP + 1, WORD_COLOUR)
    patch.paste(layer, (WORD_RIGHT - ox - layer.width, WORD_CAP_TOP - oy), layer)
    return patch


def build_pill_patch(template: Image.Image, bold: Path) -> Image.Image:
    """The type-pill patch: the pill interior repainted and TITLE set in it."""
    patch = template.crop(PILL_BOX)
    ox, oy = PILL_BOX[:2]
    box = (PILL_INTERIOR[0] - ox, PILL_INTERIOR[1] - oy, PILL_INTERIOR[2] - ox - 1, PILL_INTERIOR[3] - oy - 1)
    ImageDraw.Draw(patch).rounded_rectangle(box, radius=PILL_RADIUS, fill=PILL_FILL)
    layer = render_word(PILL_TEXT, bold, PILL_FONT_SIZE, PILL_CONDENSE, PILL_BASELINE - PILL_CAP_TOP + 1, PILL_COLOUR)
    patch.paste(layer, (round(PILL_CENTER_X - ox - layer.width / 2), PILL_CAP_TOP - oy), layer)
    return patch


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def output_path(entry: dict) -> Path:
    return ROOT / entry["path"]


def build(manifest: dict) -> dict:
    regular, bold = font_file("Liberation Serif"), font_file("Liberation Serif:bold")
    by_key = {(e["type"], e["rarity"]): e for e in manifest["outputs"]}
    uncommon = Image.open(output_path(by_key[("NOUN", "UNCOMMON")])).convert("RGB")
    common = Image.open(output_path(by_key[("NOUN", "COMMON")])).convert("RGB")
    title = Image.open(output_path(by_key[("TITLE", "COMMON")])).convert("RGB")
    word_patch = build_word_patch(uncommon, common, regular)
    pill_patch = build_pill_patch(title, bold)
    witness = title.copy()
    witness.paste(pill_patch, PILL_BOX[:2])
    return {
        "word_patch": word_patch,
        "pill_patch": pill_patch,
        "witness": witness,
        "fonts": {
            "regular": {"family": "Liberation Serif", "file": str(regular), "sha256": sha256(regular)},
            "bold": {"family": "Liberation Serif:bold", "file": str(bold), "sha256": sha256(bold)},
        },
        "sources": {
            "word": {"template": by_key[("NOUN", "UNCOMMON")]["path"], "sha256": by_key[("NOUN", "UNCOMMON")]["sha256"]},
            "word_edge": {"template": by_key[("NOUN", "COMMON")]["path"], "sha256": by_key[("NOUN", "COMMON")]["sha256"], "columns": list(WORD_EDGE_COLS)},
            "pill": {"template": by_key[("TITLE", "COMMON")]["path"], "sha256": by_key[("TITLE", "COMMON")]["sha256"]},
        },
    }


def preview(built: dict, out_dir: Path, manifest: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    by_key = {(e["type"], e["rarity"]): e for e in manifest["outputs"]}
    scale = 4
    chip = (640, 0, 848, 70)
    before = Image.open(output_path(by_key[("NOUN", "UNCOMMON")])).convert("RGB")
    after = before.copy()
    after.paste(built["word_patch"], WORD_BOX[:2])
    common = Image.open(output_path(by_key[("NOUN", "COMMON")])).convert("RGB")
    rows = [before.crop(chip), after.crop(chip), common.crop(chip)]
    sheet = Image.new("RGB", ((chip[2] - chip[0]) * scale, sum(r.height * scale + 6 for r in rows)), "white")
    y = 0
    for r in rows:
        sheet.paste(r.resize((r.width * scale, r.height * scale), Image.Resampling.LANCZOS), (0, y))
        y += r.height * scale + 6
    sheet.save(out_dir / "word-before-after-common.png")
    pill = (100, 10, 300, 70)
    tb = Image.open(output_path(by_key[("TITLE", "COMMON")])).convert("RGB")
    ta = built["witness"]
    noun = Image.open(output_path(by_key[("NOUN", "COMMON")])).convert("RGB")
    verb = Image.open(output_path(by_key[("VERB", "COMMON")])).convert("RGB")
    rows = [tb.crop(pill), ta.crop(pill), noun.crop(pill), verb.crop(pill)]
    sheet = Image.new("RGB", ((pill[2] - pill[0]) * scale, sum(r.height * scale + 6 for r in rows)), "white")
    y = 0
    for r in rows:
        sheet.paste(r.resize((r.width * scale, r.height * scale), Image.Resampling.LANCZOS), (0, y))
        y += r.height * scale + 6
    sheet.save(out_dir / "pill-before-after-noun-verb.png")
    # full header at face scale, as a card would show it
    face = after.resize((1024, 1536), Image.Resampling.LANCZOS)
    face.crop((0, 0, 1024, 120)).resize((2048, 240), Image.Resampling.LANCZOS).save(out_dir / "uncommon-header-face-scale.png")
    ta.resize((1024, 1536), Image.Resampling.LANCZOS).crop((0, 0, 1024, 120)).resize((2048, 240), Image.Resampling.LANCZOS).save(out_dir / "title-header-face-scale.png")
    print(f"previews in {out_dir}")


def asset_set_digest(templates: list[dict]) -> str:
    order = {(t, r): (TYPE_ORDER.index(t), RARITY_ORDER.index(r)) for t in TYPE_ORDER for r in RARITY_ORDER}
    lines = []
    for entry in sorted(templates, key=lambda e: order[(e["type"], e["rarity"])]):
        w, h = entry["dimensions"]
        lines.append(f"{entry['type']}\t{entry['rarity']}\t{entry['path']}\t{entry['sha256']}\t{w}x{h}\n")
    return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()


def apply(built: dict, manifest: dict) -> None:
    REPAIR_DIR.mkdir(parents=True, exist_ok=True)
    word_path = REPAIR_DIR / "uncommon-rarity-word.png"
    witness_path = REPAIR_DIR / "title-type-label-witness.png"
    built["word_patch"].save(word_path)
    built["witness"].save(witness_path)
    word_rel = word_path.relative_to(ROOT).as_posix()
    witness_rel = witness_path.relative_to(ROOT).as_posix()

    repaired = []
    for entry in manifest["outputs"]:
        image = Image.open(output_path(entry)).convert("RGB")
        changed = []
        if entry["rarity"] == "UNCOMMON":
            image.paste(built["word_patch"], WORD_BOX[:2])
            changed.append("uncommon_rarity_word_repair")
        if entry["type"] == "TITLE":
            image.paste(built["witness"].crop(PILL_BOX), PILL_BOX[:2])
            entry["type_label_source"] = witness_rel
            changed.append("paste_type_label_crop:repaired-witness")
        if not changed:
            continue
        previous = entry["sha256"]
        image.save(output_path(entry))
        entry["sha256"] = sha256(output_path(entry))
        repaired.append({"type": entry["type"], "rarity": entry["rarity"], "path": entry["path"], "previous_sha256": previous, "sha256": entry["sha256"], "stages": changed})

    stage = {
        "operation": "paste_rgb_patch",
        "applies_to_rarity": "UNCOMMON",
        "patch": word_rel,
        "patch_sha256": sha256(word_path),
        "box": list(WORD_BOX),
        "reason": "The accepted UNCOMMON rarity witness sets 'Uncommon' too wide for the block; its 'U' is clipped by the block's left edge. The patch clears the word to the block's own row profile and re-sets it to fit.",
        "construction": {
            "contract": CONTRACT,
            "script": "scripts/templates/repair_composed_labels.py",
            "source": built["sources"]["word"],
            "edge_source": built["sources"]["word_edge"],
            "clear_box": list(WORD_CLEAR),
            "profile_columns": list(WORD_PROFILE_COLS),
            "text": WORD_TEXT,
            "font": built["fonts"]["regular"],
            "font_size": WORD_FONT_SIZE,
            "condense": WORD_CONDENSE,
            "cap_rows": [WORD_CAP_TOP, WORD_BASELINE],
            "right_x": WORD_RIGHT,
            "colour": list(WORD_COLOUR),
            "supersample": SUPERSAMPLE,
            "soften": GLYPH_SOFTEN,
            "pillow": PIL.__version__,
        },
    }
    manifest["construction_stages"]["uncommon_rarity_word_repair"] = stage
    if "uncommon_rarity_word_repair" not in manifest["composition_order"]:
        manifest["composition_order"].append("uncommon_rarity_word_repair")
    manifest.setdefault("repairs", []).append({
        "date": TODAY,
        "contract": CONTRACT,
        "script": "scripts/templates/repair_composed_labels.py",
        "defects": [
            "UNCOMMON rarity word clipped by the block (all five UNCOMMON cells)",
            "TITLE cells carried the NOUN type pill (historical TITLE witness was a NOUN card)",
        ],
        "title_type_label_witness": {
            "path": witness_rel,
            "sha256": sha256(witness_path),
            "derived_from": built["sources"]["pill"],
            "pill_interior": list(PILL_INTERIOR),
            "radius": PILL_RADIUS,
            "fill": list(PILL_FILL),
            "text": PILL_TEXT,
            "font": built["fonts"]["bold"],
            "font_size": PILL_FONT_SIZE,
            "condense": PILL_CONDENSE,
            "cap_rows": [PILL_CAP_TOP, PILL_BASELINE],
            "center_x": PILL_CENTER_X,
            "colour": list(PILL_COLOUR),
        },
        "outputs": repaired,
    })
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest_digest = sha256(MANIFEST)

    persistence = json.loads(PERSISTENCE.read_text(encoding="utf-8"))
    by_key = {(e["type"], e["rarity"]): e for e in manifest["outputs"]}
    for entry in persistence["templates"]:
        source = by_key[(entry["type"], entry["rarity"])]
        entry["sha256"] = source["sha256"]
        entry["source_record"]["type_label_source"] = source["type_label_source"]
    persistence["asset_set_sha256"] = asset_set_digest(persistence["templates"])
    persistence["source"]["manifest_sha256"] = manifest_digest
    delivered = sorted(output_path(e) for e in manifest["outputs"])
    composite = hashlib.sha256("".join(sha256(p) for p in delivered).encode("utf-8")).hexdigest()
    persistence["provenance"]["delivery_composite_sha256"] = composite
    persistence["provenance"]["delivery_composite_files"] = "the 20 template PNGs, repo-relative paths sorted lexicographically"
    persistence.setdefault("repairs", []).append({"date": TODAY, "contract": CONTRACT, "composed_manifest_sha256": manifest_digest, "outputs": [r["path"] for r in repaired]})
    PERSISTENCE.write_text(json.dumps(persistence, indent=2) + "\n", encoding="utf-8")

    repin_verifier(manifest_digest, composite)
    print(json.dumps({
        "repaired": [r["path"] for r in repaired],
        "EXPECTED_SOURCE_MANIFEST_SHA256": manifest_digest,
        "EXPECTED_PROVENANCE_COMPOSITE": composite,
        "asset_set_sha256": persistence["asset_set_sha256"],
    }, indent=2))


VERIFIER = ROOT / "tools" / "verify_template_package.py"


def repin_verifier(manifest_digest: str, composite: str) -> None:
    """tools/verify_template_package.py pins the composed manifest digest and the
    delivery composite; a repair is a promotion, so it moves both pins."""
    import re

    text = VERIFIER.read_text(encoding="utf-8")
    for name, value in (("EXPECTED_SOURCE_MANIFEST_SHA256", manifest_digest), ("EXPECTED_PROVENANCE_COMPOSITE", composite)):
        pattern = re.compile(name + r' = \(\n    "[0-9a-f]{32}"\n    "[0-9a-f]{32}"\n\)')
        replacement = f'{name} = (\n    "{value[:32]}"\n    "{value[32:]}"\n)'
        text, count = pattern.subn(replacement, text)
        if count != 1:
            raise SystemExit(f"could not re-pin {name} in {VERIFIER}")
    VERIFIER.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preview", metavar="DIR", help="write close-up previews to DIR without touching the package")
    mode.add_argument("--apply", action="store_true", help="repair the package in place and re-pin the manifests")
    args = parser.parse_args(argv)
    manifest = load_manifest()
    if manifest.get("repairs"):
        raise SystemExit("the package already records a repair; refusing to stack another")
    built = build(manifest)
    if args.preview:
        preview(built, Path(args.preview), manifest)
    else:
        apply(built, manifest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
