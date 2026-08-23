#!/usr/bin/env python3
"""Build REQ-PPAUG-029 from canonical Babel data via full-face Gemini."""
from __future__ import annotations
import argparse, hashlib, json, shutil, sys
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"package"))
from hypertext.cards.example_contract import canonical_projection, load_contract, validate_projection
from hypertext.gemini.config import image_model
from hypertext.gemini.style import generate_with_styles
from hypertext.pipeline.daily import build_prompt_text

OUT=ROOT/"operator_review/req-ppaug-029-full-card-gemini"; TEMPLATES=ROOT/"templates/card/v001/composed"
EXAMPLES=ROOT/"templates/example_cards"; BASE=ROOT/"templates/card_prompt_template.json"
CONTRACT=load_contract(ROOT); TYPES=tuple(CONTRACT["variants"]); RARITIES=tuple(CONTRACT["rarities"])

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def examples(kind, rarity):
    found=[]
    for meta in sorted(EXAMPLES.glob("*/meta.yml")):
        text=meta.read_text().lower(); image=meta.parent/"outputs/card_1024x1536.png"
        if (f"card_type: {kind}" in text or f"type: {kind}" in text) and f"rarity: {rarity}" in text and image.is_file(): found.append(image)
        if len(found)==3: break
    return found

def source_records():
    records=[]; card_id=0
    for kind in TYPES:
      for rarity in RARITIES:
        for variant in range(1,4):
          card_id+=1; content,source=canonical_projection(ROOT,CONTRACT,kind,variant)
          record={"id":card_id,"type":kind,"rarity":rarity,"variant":variant,"word":content["WORD"],
                  "canonical_source":source,"authoritative_content":content}
          validate_projection(ROOT,CONTRACT,record); records.append(record)
    return records

def card_data(record):
    card=json.loads(BASE.read_text()); rarity=record["rarity"].upper(); content=dict(record["authoritative_content"])
    content.update({"NUMBER":f"{record['id']:03d}","SERIES":CONTRACT["output_series"],
                    "RARITY_TEXT":rarity,"RARITY_ICON":rarity,"TYPE":record["type"].upper()})
    card["content"]=content
    cost={"RARE":"plus one printed card icon","GLORIOUS":"plus two printed card icons"}.get(rarity,"no cost")
    card["model_prompt"] += (f" EXACT CARD TYPE: {record['type'].upper()}. The internal top-left badge must print that exact type label and its matching white icon."
      f" EXACT RARITY: {rarity}. REQUIRED COST: {cost}. Copy complete geometry from reference [1]. Render every supplied field exactly once."
      " All Hebrew/Aramaic, Greek, transliterations, glosses, senses, testament columns, and references are immutable canonical data: copy verbatim; never translate, paraphrase, approximate, decorate, or substitute them.")
    return card

def archive_output(output):
    if not output.exists(): return
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); rejected=output.parent/f"superseded-noncanonical-{stamp}"; rejected.mkdir()
    shutil.move(str(output),rejected/output.name); generation=output.with_name("generation.json")
    if generation.exists(): shutil.move(str(generation),rejected/generation.name)

def generate(ids, force):
    OUT.mkdir(parents=True,exist_ok=True); manifest_path=OUT/"provenance.json"
    old=json.loads(manifest_path.read_text()).get("records",[]) if manifest_path.exists() else []
    by_id={x["id"]:x for x in old if x.get("input_contract_version")==1}
    canonical={record["id"]:record for record in source_records()}
    for record in source_records():
        if ids and record["id"] not in ids: continue
        slug=f"{record['id']:03d}-{record['type']}-{record['rarity']}-v{record['variant']}"; case=OUT/"individual"/slug
        output=case/"outputs/card_1024x1536.png"; output.parent.mkdir(parents=True,exist_ok=True)
        card=card_data(record); prompt=build_prompt_text(card); template=TEMPLATES/record["type"]/record["rarity"]/"template_1024x1536.png"
        refs=[template,*examples(record["type"],record["rarity"])]
        (case/"card.json").write_text(json.dumps(card,ensure_ascii=False,indent=2)+"\n"); (case/"prompt.txt").write_text(prompt+"\n")
        request={"input_contract_version":1,"model":image_model(),"workflow":"hypertext.gemini.style.generate_with_styles",
          "aspect_ratio":"2:3","image_size":"2K","response_modalities":["IMAGE"],
          "template_role":"reference [1], authoritative complete geometry","canonical_source":record["canonical_source"],
          "references":[{"path":str(p.relative_to(ROOT)),"sha256":sha(p)} for p in refs],"target_type":record["type"],"target_rarity":record["rarity"]}
        (case/"request.json").write_text(json.dumps(request,indent=2)+"\n")
        if force: archive_output(output)
        if not output.exists(): generate_with_styles(prompt,[str(p) for p in refs],str(output),model=image_model(),target_rarity=record["rarity"].upper())
        by_id[record["id"]]={**record,"slug":slug,"input_contract_version":1,"card_json":str((case/"card.json").relative_to(ROOT)),
          "prompt":str((case/"prompt.txt").relative_to(ROOT)),"request":str((case/"request.json").relative_to(ROOT)),
          "output":str(output.relative_to(ROOT)),"output_sha256":sha(output),"generation":str(output.with_name("generation.json").relative_to(ROOT)),
          "generated_at":datetime.now(timezone.utc).isoformat(),"qa_status":"pending_human_review"}
        manifest={"requirement":"REQ-PPAUG-029","input_contract_version":1,"method":"build_prompt_text -> hypertext.gemini.style.generate_with_styles",
          "model":image_model(),"request":{"aspect_ratio":"2:3","image_size":"2K","response_modalities":["IMAGE"]},
          "visible_face_composition":"Gemini full-card raster only; no programmatic face drawing or overlays","schedule_enabled":False,
          "human_review_required":True,"records":[by_id[k] for k in sorted(by_id)]}
        manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")

    missing=set(canonical)-set(by_id)
    if missing:
        raise RuntimeError(
            "contract-v1 manifest remains incomplete; generate affected ids: "
            + ",".join(str(value) for value in sorted(missing))
        )

def validate():
    records=source_records()
    for record in records: validate_projection(ROOT,CONTRACT,record)
    print(json.dumps({"status":"PASS","contract_version":1,"records":len(records),
      "canonical_fields_verified":len(records)*len(CONTRACT["authoritative_fields"]),"human_review_required":True},indent=2))

def montage():
    records=json.loads((OUT/"provenance.json").read_text())["records"]
    if len(records)!=60 or any(r.get("input_contract_version")!=1 for r in records): raise RuntimeError("montage requires 60 contract-v1 cards")
    thumb=(212,316); label_h=32; margin=20; canvas=Image.new("RGB",(margin*2+12*thumb[0],margin*2+5*(thumb[1]+label_h)),"#111628")
    draw=ImageDraw.Draw(canvas); font=ImageFont.load_default(size=14)
    for row,kind in enumerate(TYPES):
      for col,record in enumerate(x for x in records if x["type"]==kind):
        x=margin+col*thumb[0]; y=margin+row*(thumb[1]+label_h); image=Image.open(ROOT/record["output"]).convert("RGB"); image.thumbnail(thumb,Image.Resampling.LANCZOS)
        canvas.paste(image,(x+(thumb[0]-image.width)//2,y)); draw.text((x+4,y+thumb[1]+7),f"{record['id']:03d} {kind.upper()} {record['rarity'].upper()} V{record['variant']}",fill="#eedcae",font=font)
    canvas.save(OUT/"review-montage-by-type-rarity.png")

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--generate",action="store_true"); parser.add_argument("--ids",help="comma-separated affected ids; default all")
    parser.add_argument("--force",action="store_true",help="archive and replace existing outputs"); parser.add_argument("--validate",action="store_true"); parser.add_argument("--montage",action="store_true"); args=parser.parse_args()
    ids={int(x) for x in args.ids.split(",")} if args.ids else set()
    if args.validate: validate()
    if args.generate: generate(ids,args.force)
    if args.montage: montage()
    if not (args.validate or args.generate or args.montage): parser.error("choose --validate, --generate, and/or --montage")
if __name__=="__main__": main()
