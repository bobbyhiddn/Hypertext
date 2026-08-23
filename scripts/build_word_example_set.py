#!/usr/bin/env python3
"""Build the deterministic REQ-PPAUG-028 review set from approved templates."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates/card/v001/composed"
OUT = ROOT / "operator_review/req-ppaug-028"
FONT = ROOT / "operator_review/assets/KaTeX_Main-Regular.ttf"
FONT_BOLD = ROOT / "operator_review/assets/KaTeX_Main-Bold.ttf"
TYPES = ["noun", "verb", "adjective", "name", "title"]
RARITIES = ["common", "uncommon", "rare", "glorious"]

WORDS = {
 "noun": [("Lamp", "A vessel that bears light", "Light makes hidden paths visible"), ("Vine", "A climbing plant that bears fruit", "Life flourishes through abiding"), ("Harbor", "A sheltered place of refuge", "Mercy receives the storm-worn")],
 "verb": [("Gather", "Bring the scattered into one", "Faithful love restores community"), ("Discern", "Perceive with wise attention", "Wisdom tests what appears true"), ("Uphold", "Sustain with steadfast strength", "Covenant faithfulness does not fail")],
 "adjective": [("Steadfast", "Firm and unwavering in purpose", "Endurance grows from rooted hope"), ("Radiant", "Shining with reflected glory", "Grace makes goodness visible"), ("Merciful", "Ready to forgive and restore", "Compassion interrupts judgment")],
 "name": [("Miriam", "Prophet and keeper of song", "Courage gives a people voice"), ("Barnabas", "Son of encouragement", "Generosity strengthens the called"), ("Lydia", "Listener with an open household", "Hospitality turns hearing into action")],
 "title": [("The Watchman", "Guardian who keeps faithful vigil", "Attention serves the vulnerable"), ("The Peacemaker", "One who repairs divided ground", "Reconciliation requires courageous truth"), ("The Wayfinder", "Guide through uncertain country", "Wisdom joins direction with patience")],
}

OT = ["Psalm 119:105 — Your word is a lamp to my feet.", "Isaiah 58:11 — You shall be like a watered garden.", "Micah 6:8 — Walk humbly with your God."]
NT = ["John 8:12 — Whoever follows me will have the light of life.", "Romans 12:2 — Be transformed by the renewing of your mind.", "James 3:17 — Wisdom from above is peaceable and full of mercy."]
HEBREW = [("אוֹר", "or — light"), ("חֶסֶד", "hesed — steadfast love"), ("שָׁלוֹם", "shalom — wholeness")]
GREEK = [("φῶς", "phos — light"), ("χάρις", "charis — grace"), ("σοφία", "sophia — wisdom")]

SCALE = 1
def s(value): return round(value * SCALE)
def sb(box): return tuple(s(v) for v in box)
def font(size: int, bold: bool = False):
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT), s(size))

def centered(draw, box, text, fnt, fill=(20, 20, 24), spacing=4):
    x0,y0,x1,y1=box
    lines=[]
    for para in text.split("\n"):
        words=para.split(); line=""
        for word in words:
            trial=(line+" "+word).strip()
            if draw.textbbox((0,0),trial,font=fnt)[2] <= x1-x0-20: line=trial
            else: lines.append(line); line=word
        if line: lines.append(line)
    heights=[draw.textbbox((0,0),s,font=fnt)[3] for s in lines]
    total=sum(heights)+spacing*max(0,len(lines)-1); y=y0+(y1-y0-total)//2
    for line,h in zip(lines,heights):
        w=draw.textbbox((0,0),line,font=fnt)[2]
        draw.text((x0+(x1-x0-w)//2,y),line,font=fnt,fill=fill)
        y += h+spacing

def clean_box(im, box):
    """Replace placeholder ink with a nearby parchment sample."""
    x0,y0,x1,y1=box
    color=im.getpixel((400,520))
    ImageDraw.Draw(im).rectangle(box,fill=color)

def art_sources():
    paths=sorted(ROOT.glob("series/**/outputs/card_1024x1536.png"))
    paths += sorted(ROOT.glob("operator_review/constrained/*/historical_faces/*/outputs/card_1024x1536.png"))
    unique=[]; seen=set()
    for p in paths:
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        if digest not in seen: seen.add(digest); unique.append(p)
    if len(unique)<60: raise RuntimeError(f"need 60 generated art sources, found {len(unique)}")
    return unique[:60]

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def build():
    cards_dir=OUT/"cards"; cards_dir.mkdir(parents=True,exist_ok=True)
    sources=art_sources(); records=[]; template_hashes={}
    index=0
    for typ in TYPES:
      for rarity in RARITIES:
        template=TEMPLATES/typ/rarity/"template_1024x1536.png"
        template_hashes[str(template.relative_to(ROOT))]=sha(template)
        for variant,(word,definition,theme) in enumerate(WORDS[typ],1):
          index+=1; image=Image.open(template).convert("RGB")
          # Clear only template placeholder zones; native labels, icon, frame and costs remain untouched.
          for box in [(210,60,640,170),(100,575,755,625),(90,685,760,735),(90,790,760,840),(65,890,410,1010),(440,890,785,1010),(65,1060,780,1170)]: clean_box(image,sb(box))
          ImageDraw.Draw(image).rectangle((35,1215,610,1255),fill=image.getpixel((700,1235)))
          source=sources[index-1]; src=Image.open(source).convert("RGB")
          artwork=ImageOps.fit(src.crop((55,200,min(800,src.width-20),425)),(740,220),method=Image.Resampling.LANCZOS)
          image.paste(artwork,(54,205)); draw=ImageDraw.Draw(image)
          centered(draw,(205,58,645,118),word.upper(),font(42,True))
          centered(draw,(205,120,645,165),definition,font(21))
          stats=((index+1)%5+1,(index+2)%5+1,(index+3)%5+1)
          draw.rectangle((55,440,795,525),fill=image.getpixel((400,520)))
          for label,cx in (("LORE",150),("CONTEXT",410),("COMPLEXITY",680)):
            centered(draw,(cx-110,440,cx+110,474),label,font(20,True))
          for sx,count in zip((71,326,590),stats):
            for j in range(5): draw.ellipse((sx+j*43,478,sx+31+j*43,509),outline=(25,36,69),width=4)
            for j in range(count): draw.ellipse((sx+j*43,478,sx+31+j*43,509),fill=(25,36,69))
          ability=f"{theme}. At {rarity} rank, this word rewards variant {variant} play."
          centered(draw,(100,575,755,625),ability,font(18))
          centered(draw,(90,685,760,735),OT[variant-1],font(17))
          centered(draw,(90,790,760,840),NT[variant-1],font(17))
          centered(draw,(70,890,405,995),HEBREW[variant-1][1].upper()+"\nHebrew witness • Psalm 119",font(18))
          centered(draw,(445,890,780,995),GREEK[variant-1][1].upper()+"\nGreek witness • John 8",font(18))
          trivia=f"• {word} joins image and meaning.\n• {theme}\n• Variant {variant} explores {rarity} play."
          draw.multiline_text((85,1070),trivia,font=font(16),fill=(20,20,24),spacing=8)
          draw.text((42,1222),f"SERIES: 2026 Q3 — EXAMPLE SET • {index:03d}/060",font=font(16),fill=(220,205,177))
          if rarity in ("rare", "glorious"):
            # Reassert the approved printed rarity/cost block after content composition.
            cost_box=(655,15,835,175)
            image.paste(Image.open(template).convert("RGB").crop(cost_box),cost_box)
          # Native type label and icon are the final authority in the upper-left.
          type_box=(20,15,210,190)
          image.paste(Image.open(template).convert("RGB").crop(type_box),type_box)
          name=f"{index:03d}-{typ}-{rarity}-v{variant}.png"; dest=cards_dir/name
          image.save(dest,optimize=True)
          prompt=(f"Compose a finished {rarity} {typ} Word Card for '{word}' from the approved {typ}/{rarity} blank; "
                  f"preserve its native badge, icon, frame, and cost; use generated source art; render canonical structured fields.")
          records.append({"id":index,"type":typ,"rarity":rarity,"variant":variant,"word":word,"definition":definition,
            "theme":theme,"ability":ability,"stats":{"lore":stats[0],"context":stats[1],"complexity":stats[2]},"ot":OT[variant-1],"nt":NT[variant-1],
            "hebrew":HEBREW[variant-1],"greek":GREEK[variant-1],"output":str(dest.relative_to(ROOT)),"output_sha256":sha(dest),
            "template":str(template.relative_to(ROOT)),"template_sha256":sha(template),"art_source":str(source.relative_to(ROOT)),
            "art_source_sha256":sha(source),"model":"repository-generated source artwork; deterministic Pillow composition",
            "prompt":prompt,"dimensions":list(image.size),"native_cost_required":rarity in ("rare","glorious")})
    (OUT/"provenance.json").write_text(json.dumps({"requirement":"REQ-PPAUG-028","schedule_enabled":False,"records":records},indent=2)+"\n")
    (OUT/"template-fingerprints.json").write_text(json.dumps(template_hashes,indent=2)+"\n")
    montage(records)

def montage(records):
    thumb=(192,288); margin=24; label_h=62; cols=12; rows=5
    canvas=Image.new("RGB",(margin*2+cols*thumb[0],margin*2+rows*(thumb[1]+label_h)),(17,22,40)); d=ImageDraw.Draw(canvas)
    for row,typ in enumerate(TYPES):
      group=[r for r in records if r["type"]==typ]
      for col,r in enumerate(group):
        x=margin+col*thumb[0]; y=margin+row*(thumb[1]+label_h)
        im=Image.open(ROOT/r["output"]).resize(thumb,Image.Resampling.LANCZOS); canvas.paste(im,(x,y))
        text=f"{typ.upper()} • {r['rarity'].upper()} • V{r['variant']}"
        d.rectangle((x,y+thumb[1],x+thumb[0],y+thumb[1]+label_h),fill=(17,22,40))
        centered(d,(x,y+thumb[1],x+thumb[0],y+thumb[1]+label_h),text,font(12,True),fill=(238,220,174))
    canvas.save(OUT/"review-montage-by-type-rarity.png",optimize=True)

if __name__ == "__main__": build()
