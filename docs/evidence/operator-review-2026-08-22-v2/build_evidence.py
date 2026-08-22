#!/usr/bin/env python3
"""Build non-overwriting visual review evidence for the corrected face contract."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
EXPECTED = (1024, 1536)

def sheet(paths, out, columns=7):
    tile, label = (256, 384), 32
    canvas = Image.new("RGB", (columns*tile[0], ((len(paths)+columns-1)//columns)*(tile[1]+label)), "#ddd6c6")
    draw = ImageDraw.Draw(canvas)
    for i, path in enumerate(paths):
        with Image.open(path) as im:
            im = im.convert("RGB").resize(tile, Image.Resampling.LANCZOS)
        x, y = i%columns*tile[0], i//columns*(tile[1]+label)
        canvas.paste(im, (x, y))
        draw.text((x+5, y+tile[1]+6), path.parent.parent.name+"/"+path.parent.name, fill="#102030", font=ImageFont.load_default())
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, "PNG")

def validate(paths):
    result=[]
    for path in paths:
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            result.append({"path":str(path.relative_to(ROOT)), "format":im.format, "mode":im.mode,
                           "size":[im.width, im.height], "accepted_file_contract":im.format=="PNG" and im.size==EXPECTED})
    return result

def main():
    templates=sorted((ROOT/"templates/card/v001").glob("*/template_1024x1536.png"))+sorted((ROOT/"templates/lot/v001").glob("*/template_1024x1536.png"))
    samples=sorted((HERE/"sample").glob("*/outputs/*_1024x1536.png"))
    if len(templates)!=14: raise SystemExit(f"expected 14 templates, got {len(templates)}")
    sheet(templates, HERE/"contact-sheets/templates-v2.png")
    if samples: sheet(samples, HERE/"contact-sheets/validation-sample-v2.png", columns=len(samples))
    report={"visual_acceptance":"manual; file validity alone is insufficient", "templates":validate(templates), "sample":validate(samples)}
    (HERE/"image-validation-v2.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")

if __name__=="__main__": main()
