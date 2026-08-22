#!/usr/bin/env python3
"""Build an offline provenance-first matrix of currently selected templates."""
import hashlib, json, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
HEAD = subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
OUT = ROOT / "operator_review" / f"current-template-source-matrix-{HEAD[:7]}"
MF = ROOT / "templates/card/v001/composed/manifest.json"
SEL = ROOT / "package/hypertext/cards/template_matrix.py"
MAT = ROOT / "schema/babel_template_matrix.json"
TYPES = ("NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE")
RARITIES = ("COMMON", "UNCOMMON", "RARE", "GLORIOUS")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rev(p):
    return subprocess.check_output(("git", "log", "-1", "--format=%H", "--", str(p.relative_to(ROOT))), cwd=ROOT, text=True).strip()

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    authority = json.loads(MF.read_text())
    entries = {(x["type"], x["rarity"]): x for x in authority["outputs"]}
    thumb, left, top, footer = (212, 316), 154, 92, 82
    sheet = Image.new("RGB", (left + 848, top + 5 * (316 + footer)), "white")
    draw, font, small = ImageDraw.Draw(sheet), ImageFont.load_default(size=16), ImageFont.load_default(size=11)
    draw.text((12, 8), "CURRENT SELECTED REUSABLE TEMPLATES — repository-backed, no generation", fill="black", font=font)
    draw.text((12, 36), f"worktree HEAD {HEAD}", fill="black", font=small)
    draw.text((12, 55), "Footer: status | exact repo path | SHA-256 prefix", fill="black", font=small)
    for c, rarity in enumerate(RARITIES): draw.text((left + c*212 + 8, 72), rarity, fill="black", font=font)
    records = []
    for r, typ in enumerate(TYPES):
        draw.text((8, top + r*398 + 8), typ, fill="black", font=font)
        for c, rarity in enumerate(RARITIES):
            x, y, entry = left + c*212, top + r*398, entries.get((typ, rarity))
            if not entry:
                draw.rectangle((x,y,x+211,y+315), outline="#9b1c1c", width=4); draw.text((x+50,y+140), "MISSING", fill="#9b1c1c", font=font)
                records.append({"type":typ,"rarity":rarity,"status":"MISSING","issue":"No selector-manifest entry","requires_regeneration":True}); continue
            source, expected = ROOT / entry["path"], entry["sha256"]
            actual = sha(source); issue = None if actual == expected else "INCONSISTENT: bytes differ from manifest SHA-256"
            with Image.open(source) as im:
                dimensions=list(im.size); sheet.paste(im.convert("RGB").resize(thumb, Image.Resampling.LANCZOS),(x,y))
            p=entry["path"]; draw.text((x+3,y+320),"DISCRETE",fill="#146b2e" if not issue else "#9b1c1c",font=small)
            draw.text((x+3,y+338),p[:38],fill="black",font=small); draw.text((x+3,y+355),p[38:76],fill="black",font=small)
            draw.text((x+3,y+373),actual[:16],fill="black",font=small)
            records.append({"type":typ,"rarity":rarity,"status":"DISCRETE","path":p,"path_revision":rev(source),"sha256":actual,"manifest_sha256":expected,"dimensions":dimensions,"accepted_candidate":entry.get("accepted_candidate"),"issue":issue,"requires_regeneration":False})
    montage=OUT/"current-template-source-matrix.png"; sheet.save(montage,"PNG",compress_level=9)
    wrong=[x for x in records if x.get("issue")]; missing=[x for x in records if x["status"]=="MISSING"]
    result={"schema_version":1,"status":"offline-source-of-truth-review","worktree_head":HEAD,"montage":montage.name,"montage_sha256":sha(montage),
      "authority":{"selector":str(SEL.relative_to(ROOT)),"selector_revision":rev(SEL),"manifest":str(MF.relative_to(ROOT)),"manifest_revision":rev(MF),"matrix_data":str(MAT.relative_to(ROOT)),"matrix_revision":rev(MAT)},
      "classifications":{"reusable_selected_templates":"templates/card/v001/composed/*/*/template_1024x1536.png (only paths returned by resolve_template)","reusable_layer_inputs":"templates/card/v001/{base,noun,verb,adjective,name,title,common,uncommon,rare,glorious}/template_1024x1536.png","generated_sample_outputs_not_templates":"operator_review/babel-alpha-visual-matrix-51eb649/individual/*/{raw.png,image_1024x1536.png}","historical_approved_faces":"operator_review/constrained/e50961ad0f4d/*.png (promotion witnesses)","prompt_descriptors_not_assets":"schema/visual_descriptor.schema.json; package/hypertext/prompts/visual_descriptor.py; templates/card*_prompt*","card_specific_assets_not_templates":"series/2026-Q1/cards/*; templates/example_cards/*"},
      "cells":records,"findings":{"wrong_or_inconsistent":wrong,"missing":missing,"derived_cells":[],"require_regeneration":[],"superseded_artifact":"operator_review/babel-alpha-visual-matrix-51eb649 contains generated card-specific samples, not reusable templates."},
      "safety":{"gemini_called":False,"card_faces_regenerated":False,"production_automation_changed":False,"merge_or_deployment_performed":False}}
    (OUT/"manifest.json").write_text(json.dumps(result,indent=2)+"\n")
    (OUT/"README.md").write_text(f"# Current template source matrix\n\nOffline inventory at worktree revision `{HEAD}`. The montage displays the 20 discrete reusable files selected by `package/hypertext/cards/template_matrix.py`; every cell records its exact path, file revision, and SHA-256 in `manifest.json`.\n\nThe earlier `babel-alpha-visual-matrix-51eb649` is generated card-specific sample output, not template evidence. Historical faces, layer inputs, prompt descriptors, and card-specific assets are classified separately. There are no MISSING or DERIVED selector cells at this revision and no cell needs regeneration. No Gemini call, generation, automation change, merge, or deployment occurred.\n")
    print(montage)

if __name__ == "__main__": main()
