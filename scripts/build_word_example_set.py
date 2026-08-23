#!/usr/bin/env python3
"""Generate REQ-PPAUG-029 through Hypertext's native full-card Gemini path."""
from __future__ import annotations
import argparse, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"package"))
from hypertext.gemini.config import image_model
from hypertext.gemini.style import generate_with_styles
from hypertext.pipeline.daily import build_prompt_text

SOURCE=ROOT/"operator_review/req-ppaug-028/provenance.json"
OUT=ROOT/"operator_review/req-ppaug-029-full-card-gemini"
TEMPLATES=ROOT/"templates/card/v001/composed"; EXAMPLES=ROOT/"templates/example_cards"
BASE=ROOT/"templates/card_prompt_template.json"
TYPES=("noun","verb","adjective","name","title"); RARITIES=("common","uncommon","rare","glorious")

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def examples(typ,rarity):
    found=[]
    for meta in sorted(EXAMPLES.glob("*/meta.yml")):
        text=meta.read_text().lower(); image=meta.parent/"outputs/card_1024x1536.png"
        if (f"card_type: {typ}" in text or f"type: {typ}" in text) and f"rarity: {rarity}" in text and image.is_file(): found.append(image)
        if len(found)==3: break
    return found

def card_data(r):
    card=json.loads(BASE.read_text()); rarity=r["rarity"].upper()
    heb,hebt=r["hebrew"]; greek,greekt=r["greek"]
    card["content"]={"NUMBER":f"{r['id']:03d}","SERIES":"2026 Q3 — REQ-PPAUG-029 EXAMPLE SET","WORD":r["word"].upper(),
      "GLOSS":r["definition"],"CARD_TYPE":r["type"].upper(),"TYPE":r["type"].upper(),"RARITY_TEXT":rarity,"RARITY_ICON":rarity,
      "ART_PROMPT":f"One coherent biblical-era symbolic scene expressing {r['word']}: {r['theme'].lower()}, painterly illuminated-manuscript realism, no text",
      "ABILITY_TEXT":r["ability"],"STAT_LORE":r["stats"]["lore"],"STAT_CONTEXT":r["stats"]["context"],"STAT_COMPLEXITY":r["stats"]["complexity"],
      "OT_VERSE_LINE":r["ot"],"NT_VERSE_LINE":r["nt"],"HEBREW":heb,"HEBREW_TRANSLIT":hebt,"GREEK":greek,"GREEK_TRANSLIT":greekt,
      "OT_REFS":r["ot"].split(" — ",1)[0],"NT_REFS":r["nt"].split(" — ",1)[0],
      "TRIVIA_BULLETS":[f"{r['word']} joins image and meaning.",r["theme"],f"Variant {r['variant']} of the {rarity.lower()} example."]}
    cost={"RARE":"plus one printed card icon","GLORIOUS":"plus two printed card icons"}.get(rarity,"no cost")
    card["model_prompt"] += (f" EXACT CARD TYPE: {r['type'].upper()}. The internal top-left badge must print that exact type label and its matching white icon."
      f" EXACT RARITY: {rarity}. REQUIRED COST: {cost}. Copy complete geometry from reference [1]. Render every supplied field once only.")
    return card

def source_records():
    records=json.loads(SOURCE.read_text())["records"]
    counts={(t,q):0 for t in TYPES for q in RARITIES}
    for r in records: counts[(r["type"],r["rarity"])]+=1
    if len(records)!=60 or set(counts.values())!={3}: raise RuntimeError(f"source is not 5 x 4 x 3: {len(records)}, {counts}")
    return records

def generate(limit,start):
    OUT.mkdir(parents=True,exist_ok=True); mp=OUT/"provenance.json"
    manifest={"requirement":"REQ-PPAUG-029","method":"build_prompt_text -> hypertext.gemini.style.generate_with_styles",
      "model":image_model(),"request":{"aspect_ratio":"2:3","image_size":"2K","response_modalities":["IMAGE"]},
      "visible_face_composition":"Gemini full-card raster only; no programmatic face drawing or overlays","schedule_enabled":False,"records":[]}
    if mp.exists(): manifest["records"]=json.loads(mp.read_text()).get("records",[])
    by_id={x["id"]:x for x in manifest["records"]}; attempted=0
    for r in source_records():
        if r["id"]<start or (limit is not None and attempted>=limit): continue
        attempted+=1; slug=f"{r['id']:03d}-{r['type']}-{r['rarity']}-v{r['variant']}"; case=OUT/"individual"/slug
        output=case/"outputs/card_1024x1536.png"; output.parent.mkdir(parents=True,exist_ok=True)
        card=card_data(r); prompt=build_prompt_text(card); template=TEMPLATES/r["type"]/r["rarity"]/"template_1024x1536.png"; refs=[template,*examples(r["type"],r["rarity"])]
        (case/"card.json").write_text(json.dumps(card,ensure_ascii=False,indent=2)+"\n"); (case/"prompt.txt").write_text(prompt+"\n")
        req={"model":image_model(),"workflow":"hypertext.gemini.style.generate_with_styles","template_role":"reference [1], authoritative complete geometry",
          "references":[{"path":str(p.relative_to(ROOT)),"sha256":sha(p)} for p in refs],"target_type":r["type"],"target_rarity":r["rarity"]}
        (case/"request.json").write_text(json.dumps(req,indent=2)+"\n")
        if not output.is_file(): generate_with_styles(prompt,[str(p) for p in refs],str(output),model=image_model(),target_rarity=r["rarity"].upper())
        generation=output.with_name("generation.json")
        by_id[r["id"]]={"id":r["id"],"slug":slug,"type":r["type"],"rarity":r["rarity"],"variant":r["variant"],"word":r["word"],
          "card_json":str((case/"card.json").relative_to(ROOT)),"prompt":str((case/"prompt.txt").relative_to(ROOT)),"request":str((case/"request.json").relative_to(ROOT)),
          "output":str(output.relative_to(ROOT)),"output_sha256":sha(output),"generation":str(generation.relative_to(ROOT)),
          "generated_at":datetime.now(timezone.utc).isoformat(),"qa_status":"pending_visual_review"}
        manifest["records"]=[by_id[k] for k in sorted(by_id)]; mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")

def montage():
    records=json.loads((OUT/"provenance.json").read_text())["records"]
    if len(records)!=60: raise RuntimeError(f"montage requires 60 generated cards, found {len(records)}")
    thumb=(212,316); lh=32; margin=20; canvas=Image.new("RGB",(margin*2+12*thumb[0],margin*2+5*(thumb[1]+lh)),"#111628")
    draw=ImageDraw.Draw(canvas); font=ImageFont.load_default(size=14)
    for row,typ in enumerate(TYPES):
      for col,r in enumerate(x for x in records if x["type"]==typ):
        x=margin+col*thumb[0]; y=margin+row*(thumb[1]+lh); im=Image.open(ROOT/r["output"]).convert("RGB"); im.thumbnail(thumb,Image.Resampling.LANCZOS)
        canvas.paste(im,(x+(thumb[0]-im.width)//2,y)); draw.text((x+4,y+thumb[1]+7),f"{r['id']:03d} {typ.upper()} {r['rarity'].upper()} V{r['variant']}",fill="#eedcae",font=font)
    canvas.save(OUT/"review-montage-by-type-rarity.png")

def main():
    p=argparse.ArgumentParser(); p.add_argument("--generate",action="store_true"); p.add_argument("--limit",type=int); p.add_argument("--start",type=int,default=1); p.add_argument("--montage",action="store_true"); a=p.parse_args()
    if a.generate: generate(a.limit,a.start)
    if a.montage: montage()
    if not a.generate and not a.montage: p.error("choose --generate and/or --montage")
if __name__=="__main__": main()
