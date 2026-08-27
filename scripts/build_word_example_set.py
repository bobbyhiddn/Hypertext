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
REJECTIONS=OUT/"visual-rejections.json"; QA=OUT/"qa-summary.json"; VALIDATION=OUT/"validation-report.json"
VISUAL_BENCHMARK_VERSION="see-v4"
VISUAL_BENCHMARK=ROOT/"operator_review/req-ppaug-030-see-benchmark/pilot-see-v4/outputs/card_1024x1536.png"
LANGUAGE_BENCHMARK=ROOT/"operator_review/req-ppaug-030-see-benchmark/printed-see-languages-reference.png"
RENDER_CONTRACT_VERSION=4
SUPPORTED_RENDER_CONTRACT_VERSIONS=(2,3,RENDER_CONTRACT_VERSION)
CONTRACT=load_contract(ROOT); TYPES=tuple(CONTRACT["variants"]); RARITIES=tuple(CONTRACT["rarities"])

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def examples(kind, rarity):
    found=[]
    for meta in sorted(EXAMPLES.glob("*/meta.yml")):
        text=meta.read_text().lower(); image=meta.parent/"outputs/card_1024x1536.png"
        if (f"card_type: {kind}" in text or f"type: {kind}" in text) and f"rarity: {rarity}" in text and image.is_file(): found.append(image)
        if len(found)==3: break
    return found

def reference_inputs(record):
    template=TEMPLATES/record["type"]/record["rarity"]/"template_1024x1536.png"
    matching_examples=examples(record["type"],record["rarity"])
    if not matching_examples:
        raise RuntimeError(f"missing historical style example for {record['type']}/{record['rarity']}")
    refs=[template,VISUAL_BENCHMARK,matching_examples[0],LANGUAGE_BENCHMARK]
    roles=("authoritative type/rarity geometry","accepted SEE v4 visual benchmark",
           "historical matching type/rarity style","operator-accepted printed SEE Languages-region benchmark")
    return refs,roles

def codepoints(value):
    return " ".join(f"U+{ord(character):04X}" for character in value)

def reference_line_contract(label, value):
    """Give Gemini an unambiguous compact wrap without changing canonical text."""
    references=value.split(" • ")
    if len(references)<3:
        return f"{label} REFERENCE LAYOUT: render the complete value on one line with no leading list marker."
    first_line=f"{label} Refs: {' • '.join(references[:2])} •"
    second_line=" • ".join(references[2:])
    return (f"{label} REFERENCE LAYOUT: render exactly two centered lines. Line 1 is '{first_line}'. "
            f"Line 2 is '{second_line}'. Neither line begins with a bullet or list marker; the terminal "
            "bullet on line 1 is the separator before the first reference on line 2.")

def exact_render_contract(record, content):
    rarity=record["rarity"].upper()
    cost={"COMMON":"zero printed card-cost icons","UNCOMMON":"zero printed card-cost icons",
          "RARE":"exactly one printed card-cost icon","GLORIOUS":"exactly two printed card-cost icons"}[rarity]
    labels=("ABILITY","OT VERSE","NT VERSE","HEBREW/ARAMAIC","GREEK","TRIVIA")
    trivia="\n".join(f"TRIVIA {index}: {value}" for index,value in enumerate(content["TRIVIA_BULLETS"],1))
    figure_rule=(
      "ART FIGURE RULE: show no person or human body at all; communicate this person-linked word only through objects, work, environment, symbols, or achievements."
      if record["type"]=="name" or content["WORD"]=="BROTHER"
      else "ART FIGURE RULE: no recognizable face or portrait likeness."
    )
    return "\n".join((
      f"EXACT FULL-FACE RENDER CONTRACT v{RENDER_CONTRACT_VERSION}:",
      "The values below are printed content, not suggestions. Reproduce every character and punctuation mark exactly once. Do not add quotation marks, labels, glosses, ellipses, or punctuation that is absent from a value, and do not remove any that is present.",
      f"HEADER: #{content['NUMBER']} | {record['type'].upper()} | {rarity} | {content['WORD']}",
      f"TYPE CONTRACT: use the exact {record['type'].upper()} badge, white medallion icon, and geometry from image [1]; never borrow VERB or SEE header details.",
      f"RARITY CONTRACT: print the exact all-uppercase token {rarity}, Unicode {codepoints(rarity)}, with {cost}. Copy the badge geometry, color, diamond, and cost placement from image [1], but not its placeholder lettercase. Forbidden alternatives include title case, 'RARITY:', or any added word.",
      "COST ICON CONTRACT: every printed card-cost icon is a plain dark outlined card stack. Never put a cross, letter, number, or other symbol inside it. Keep the complete Babel face geometry from image [1]; never switch to an alternate card layout.",
      f"STAT CONTRACT: each row has exactly five circular pips. LORE={content['STAT_LORE']} filled and {5-content['STAT_LORE']} empty; CONTEXT={content['STAT_CONTEXT']} filled and {5-content['STAT_CONTEXT']} empty; COMPLEXITY={content['STAT_COMPLEXITY']} filled and {5-content['STAT_COMPLEXITY']} empty.",
      "SECTION LABELS, EXACTLY: " + " | ".join(labels),
      f"GLOSS, EXACT: {content['GLOSS']}",
      f"ABILITY, EXACT: {content['ABILITY_TEXT']}",
      f"OT VERSE, EXACT: {content['OT_VERSE_LINE']}",
      f"OT VERSE UNICODE SEQUENCE: {codepoints(content['OT_VERSE_LINE'])}",
      f"NT VERSE, EXACT: {content['NT_VERSE_LINE']}",
      f"NT VERSE UNICODE SEQUENCE: {codepoints(content['NT_VERSE_LINE'])}",
      f"VERSE PUNCTUATION RULE: OT has exactly {content['OT_VERSE_LINE'].count('“')} U+201C and {content['OT_VERSE_LINE'].count('”')} U+201D quote marks; NT has exactly {content['NT_VERSE_LINE'].count('“')} U+201C and {content['NT_VERSE_LINE'].count('”')} U+201D quote marks. If a count is zero, render no quote glyph there. Never add decorative quotation marks or ellipses.",
      f"HEBREW/ARAMAIC, EXACT: {content['HEBREW']}",
      f"HEBREW/ARAMAIC UNICODE SEQUENCE: {codepoints(content['HEBREW'])}",
      f"HEBREW TRANSLITERATION, EXACT: {content['HEBREW_TRANSLIT']}",
      f"HEBREW TRANSLITERATION UNICODE SEQUENCE: {codepoints(content['HEBREW_TRANSLIT'])}",
      f"GREEK, EXACT: {content['GREEK']}",
      f"GREEK UNICODE SEQUENCE: {codepoints(content['GREEK'])}",
      f"GREEK TRANSLITERATION, EXACT: {content['GREEK_TRANSLIT']}",
      f"GREEK TRANSLITERATION UNICODE SEQUENCE: {codepoints(content['GREEK_TRANSLIT'])}",
      f"OT REFERENCE BLOCK, EXACT COMPLETE VALUE: OT Refs: {content['OT_REFS']}",
      f"OT REFERENCE BULLET CONTRACT: exactly {content['OT_REFS'].count('•')} literal U+2022 bullets in the complete block; a line wrap never replaces a bullet.",
      reference_line_contract("OT",content["OT_REFS"]),
      f"NT REFERENCE BLOCK, EXACT COMPLETE VALUE: NT Refs: {content['NT_REFS']}",
      f"NT REFERENCE BULLET CONTRACT: exactly {content['NT_REFS'].count('•')} literal U+2022 bullets in the complete block; a line wrap never replaces a bullet.",
      reference_line_contract("NT",content["NT_REFS"]),
      trivia,
      f"FOOTER, EXACT: SERIES: {content['SERIES']}",
      "LANGUAGES GEOMETRY: one compact equal-width two-column panel. Left header is exactly HEBREW/ARAMAIC; right header is exactly GREEK. Native script is large, bare italic transliteration follows, then the complete Refs line. Never print ORIGINAL LANGUAGES, TRANSLIT, definitions, parentheses, or English glosses in this panel.",
      f"ART CONTRACT: depict the supplied ART_PROMPT sense for {content['WORD']} symbolically. Show no readable text in the art. If a person is implicated, represent what the person is known for through objects, work, attire, environment, symbols, or achievements; use no recognizable face or portrait likeness.",
      figure_rule,
      "FINAL SELF-CHECK BEFORE RETURNING THE IMAGE: exact type icon, rarity and cost, all fifteen pips, all immutable text, both reference bullet counts, compact Languages panel, no separator loss, no placeholder, no overlap, and no recognizable face.",
    ))

def valid_previous_record(record):
    if (record.get("input_contract_version")!=1
            or record.get("visual_descriptor_version")!=2
            or record.get("visual_benchmark_version")!=VISUAL_BENCHMARK_VERSION
            or record.get("render_contract_version") not in SUPPORTED_RENDER_CONTRACT_VERSIONS):
        return False
    try:
        paths={name:ROOT/record[name] for name in ("card_json","prompt","request","output")}
        expected={
            "card_json":"card_sha256",
            "prompt":"prompt_sha256",
            "request":"request_sha256",
            "output":"output_sha256",
        }
        return all(path.is_file() and sha(path)==record[expected[name]] for name,path in paths.items())
    except (KeyError, OSError):
        return False

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
      " All Hebrew/Aramaic, Greek, transliterations, glosses, senses, testament columns, and references are immutable canonical data: copy verbatim; never translate, paraphrase, approximate, decorate, or substitute them."
      " Never print placeholder, schema, field-name, or instruction labels such as DEFINITION TEXT, GLOSS, ART PROMPT, TYPE, or TRANSLIT.")
    return card

def archive_output(output, *, stamp=None):
    if not output.exists(): return None
    stamp=stamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rejected=output.parent/f"superseded-noncanonical-{stamp}"
    suffix=1
    while rejected.exists():
        rejected=output.parent/f"superseded-noncanonical-{stamp}-{suffix}"; suffix+=1
    rejected.mkdir()
    shutil.move(str(output),rejected/output.name); generation=output.with_name("generation.json")
    if generation.exists(): shutil.move(str(generation),rejected/generation.name)
    return rejected/output.name

def benchmark_prompt(record,card,*,fix_notes=None):
    prompt=build_prompt_text(card)
    if fix_notes:
        roles=(
          "Image [1] is the rejected full face being corrected. Preserve every already-correct character, panel, separator, icon, pip, and artwork detail except the explicitly rejected issues below.",
          "Image [2] is authoritative for this card's complete type/rarity geometry, badge, icon, rarity treatment, and printed cost. Copy no placeholder text from it.",
          "Image [3] is the accepted SEE v4 benchmark. Match its restrained printed Babel finish, compact panel density, small typography, symbolic no-face art, and two-column Languages hierarchy. Copy none of its content.",
          "Image [4] is a historical Babel face matching this type and rarity. Use only its visual vocabulary; copy no content and do not reproduce a recognizable human face.",
          "Image [5] is only the operator-accepted printed SEE Languages-region crop. It is authoritative only for that compact panel's hierarchy, line breaks, separators, and density.",
          "NATIVE FULL-FACE CORRECTION: return one wholly regenerated 1024x1536 card face. Do not composite, trace, paste, mask, or overlay visible pixels from any reference.",
          "EXPLICIT VISUAL REJECTIONS TO CORRECT:",
          *(f"- {note}" for note in fix_notes),
          "Everything not named above remains immutable. Recheck the complete render contract after making the corrections.",
        )
    else:
        roles=(
          "Image [1] is authoritative for this card's complete type/rarity geometry, badge, icon, rarity treatment, and printed cost. Copy no text from it.",
          "Image [2] is the accepted SEE v4 benchmark. Match its restrained printed Babel finish, compact panel density, small typography, symbolic no-face art, and two-column Languages hierarchy. Copy none of its word, number, type, rarity, stats, verses, lexemes, references, or trivia.",
          "Image [3] is a historical Babel face matching this type and rarity. Use only its visual vocabulary; copy no content and do not reproduce a recognizable human face.",
          "Image [4] is only the operator-accepted printed SEE Languages-region crop. It is authoritative only for that compact panel's hierarchy, line breaks, separators, and density; infer nothing about any other card region from it.",
          "Render one wholly new full-card raster. Do not composite, trace, paste, or overlay visible pixels from any reference.",
        )
    return prompt+"\n"+"\n".join(("ACCEPTED BENCHMARK REFERENCE ROLES:",*roles,exact_render_contract(record,card["content"])))

def generate(ids, force):
    for benchmark in (VISUAL_BENCHMARK,LANGUAGE_BENCHMARK):
        if not benchmark.is_file():
            raise RuntimeError(f"missing accepted visual benchmark: {benchmark}")
    OUT.mkdir(parents=True,exist_ok=True); manifest_path=OUT/"provenance.json"
    old=json.loads(manifest_path.read_text()).get("records",[]) if manifest_path.exists() else []
    by_id={x["id"]:x for x in old if valid_previous_record(x)}
    canonical={record["id"]:record for record in source_records()}
    for record in source_records():
        if ids and record["id"] not in ids: continue
        slug=f"{record['id']:03d}-{record['type']}-{record['rarity']}-v{record['variant']}"; case=OUT/"individual"/slug
        output=case/"outputs/card_1024x1536.png"; output.parent.mkdir(parents=True,exist_ok=True)
        card=card_data(record); prompt=benchmark_prompt(record,card); refs,roles=reference_inputs(record)
        card_path=case/"card.json"; prompt_path=case/"prompt.txt"; request_path=case/"request.json"
        card_path.write_text(json.dumps(card,ensure_ascii=False,indent=2)+"\n"); prompt_path.write_text(prompt+"\n")
        request={"input_contract_version":1,"visual_descriptor_version":2,"visual_benchmark_version":VISUAL_BENCHMARK_VERSION,
          "render_contract_version":RENDER_CONTRACT_VERSION,
          "model":image_model(),"workflow":"hypertext.gemini.style.generate_with_styles",
          "aspect_ratio":"2:3","image_size":"2K","response_modalities":["IMAGE"],
          "template_role":"reference [1], authoritative complete geometry","canonical_source":record["canonical_source"],
          "locked_visual_benchmark":{"path":str(VISUAL_BENCHMARK.relative_to(ROOT)),"sha256":sha(VISUAL_BENCHMARK)},
          "references":[{"role":role,"path":str(p.relative_to(ROOT)),"sha256":sha(p)} for role,p in zip(roles,refs,strict=True)],
          "target_type":record["type"],"target_rarity":record["rarity"]}
        request_path.write_text(json.dumps(request,indent=2)+"\n")
        previous=by_id.get(record["id"])
        prior_fix_history=list(previous.get("fix_history",[])) if previous else []
        prior_regeneration_history=list(previous.get("regeneration_history",[])) if previous else []
        archived=None; source_sha=None
        reusable=(not force and previous is not None
                  and previous.get("card_sha256")==sha(card_path)
                  and previous.get("prompt_sha256")==sha(prompt_path)
                  and previous.get("request_sha256")==sha(request_path))
        if not reusable:
            by_id.pop(record["id"],None)
            source_sha=sha(output) if output.is_file() else None
            archived=archive_output(output)
            generate_with_styles(prompt,[str(p) for p in refs],str(output),model=image_model(),target_rarity=record["rarity"].upper())
        current={**record,"slug":slug,"input_contract_version":1,"visual_descriptor_version":2,
          "render_contract_version":RENDER_CONTRACT_VERSION,
          "visual_benchmark_version":VISUAL_BENCHMARK_VERSION,"card_json":str(card_path.relative_to(ROOT)),
          "card_sha256":sha(card_path),"prompt":str(prompt_path.relative_to(ROOT)),"prompt_sha256":sha(prompt_path),
          "request":str(request_path.relative_to(ROOT)),"request_sha256":sha(request_path),
          "output":str(output.relative_to(ROOT)),"output_sha256":sha(output),"generation":str(output.with_name("generation.json").relative_to(ROOT)),
          "generated_at":datetime.now(timezone.utc).isoformat(),"qa_status":"pending_human_review"}
        if prior_fix_history: current["fix_history"]=prior_fix_history
        if archived is not None:
            regeneration={"reason":"fresh native full-face regeneration after visual rejection",
                          "source_output_sha256":source_sha,
                          "archived_output":str(archived.relative_to(ROOT))}
            current["regeneration_history"]=[*prior_regeneration_history,regeneration]
        elif prior_regeneration_history:
            current["regeneration_history"]=prior_regeneration_history
        by_id[record["id"]]=current
        manifest={"requirement":"REQ-PPAUG-029","input_contract_version":1,"visual_descriptor_version":2,
          "render_contract_version":RENDER_CONTRACT_VERSION,
          "visual_benchmark_version":VISUAL_BENCHMARK_VERSION,"visual_benchmark":str(VISUAL_BENCHMARK.relative_to(ROOT)),
          "method":"build_prompt_text -> hypertext.gemini.style.generate_with_styles",
          "model":image_model(),"request":{"aspect_ratio":"2:3","image_size":"2K","response_modalities":["IMAGE"]},
          "visible_face_composition":"Gemini full-card raster only; no programmatic face drawing or overlays","schedule_enabled":False,
          "human_review_required":True,"records":[by_id[k] for k in sorted(by_id)]}
        manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")

    missing=set(canonical)-set(by_id)
    if missing and not ids:
        raise RuntimeError(
            "contract-v1 manifest remains incomplete; generate affected ids: "
            + ",".join(str(value) for value in sorted(missing))
        )
    if missing:
        print(json.dumps({"status":"PARTIAL","generated_records":len(by_id),
                          "remaining_ids":sorted(missing)},indent=2))

def fix_rejected(ids):
    """Regenerate rejected faces through the native full-card Gemini edit path."""
    for benchmark in (VISUAL_BENCHMARK,LANGUAGE_BENCHMARK):
        if not benchmark.is_file():
            raise RuntimeError(f"missing accepted visual benchmark: {benchmark}")
    if not REJECTIONS.is_file():
        raise RuntimeError(f"missing visual rejection evidence: {REJECTIONS}")
    rejection_data=json.loads(REJECTIONS.read_text())
    rejected={item["id"]:item for item in rejection_data.get("rejections",[])}
    if ids: rejected={card_id:item for card_id,item in rejected.items() if card_id in ids}
    if not rejected: raise RuntimeError("no rejected cards selected")
    manifest_path=OUT/"provenance.json"; manifest=json.loads(manifest_path.read_text())
    by_id={item["id"]:item for item in manifest.get("records",[]) if valid_previous_record(item)}
    for previous_record in by_id.values():
        if previous_record.get("source_rejection") and not previous_record.get("fix_history"):
            previous_record["fix_history"]=[previous_record["source_rejection"]]
    canonical={record["id"]:record for record in source_records()}
    missing=set(rejected)-set(by_id)
    if missing: raise RuntimeError(f"rejected ids lack hash-valid current bundles: {sorted(missing)}")
    unknown=set(rejected)-set(canonical)
    if unknown: raise RuntimeError(f"unknown rejected ids: {sorted(unknown)}")
    for card_id,item in sorted(rejected.items()):
        record=canonical[card_id]; previous=by_id[card_id]; output=ROOT/previous["output"]
        notes=item.get("issues",[])
        if not notes or not all(isinstance(note,str) and note.strip() for note in notes):
            raise RuntimeError(f"rejected card {card_id} has no actionable visual issue")
        expected=item.get("output_sha256")
        if expected and expected!=sha(output):
            raise RuntimeError(f"rejection evidence is stale for card {card_id}")
        card=card_data(record); prompt=benchmark_prompt(record,card,fix_notes=notes)
        base_refs,base_roles=reference_inputs(record); refs=[output,*base_refs]
        stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        case=OUT/"individual"/previous["slug"]; pending=case/f".pending-fix-{stamp}"
        candidate=pending/"outputs/card_1024x1536.png"; candidate.parent.mkdir(parents=True)
        source_sha=sha(output)
        generate_with_styles(prompt,[str(path) for path in refs],str(candidate),model=image_model(),
                             target_rarity=record["rarity"].upper(),fix_mode=True)
        archived=archive_output(output,stamp=stamp)
        if archived is None: raise RuntimeError(f"lost current fix source for card {card_id}")
        shutil.move(str(candidate),output); shutil.move(str(candidate.with_name("generation.json")),output.with_name("generation.json"))
        candidate.parent.rmdir(); pending.rmdir()
        card_path=case/"card.json"; prompt_path=case/"prompt.txt"; request_path=case/"request.json"
        card_path.write_text(json.dumps(card,ensure_ascii=False,indent=2)+"\n"); prompt_path.write_text(prompt+"\n")
        fixed_refs=[archived,*base_refs]; fixed_roles=("rejected full face corrected by native Gemini fix mode",*base_roles)
        request={"input_contract_version":1,"visual_descriptor_version":2,
          "visual_benchmark_version":VISUAL_BENCHMARK_VERSION,"render_contract_version":RENDER_CONTRACT_VERSION,
          "model":image_model(),"workflow":"hypertext.gemini.style.generate_with_styles/fix_mode",
          "fix_mode":True,"full_face_generation_only":True,"visible_pixel_composition":False,
          "aspect_ratio":"2:3","image_size":"2K","response_modalities":["IMAGE"],
          "canonical_source":record["canonical_source"],"corrections":notes,
          "source_output_sha256":source_sha,
          "locked_visual_benchmark":{"path":str(VISUAL_BENCHMARK.relative_to(ROOT)),"sha256":sha(VISUAL_BENCHMARK)},
          "references":[{"role":role,"path":str(path.relative_to(ROOT)),"sha256":sha(path)}
                        for role,path in zip(fixed_roles,fixed_refs,strict=True)],
          "target_type":record["type"],"target_rarity":record["rarity"]}
        request_path.write_text(json.dumps(request,indent=2)+"\n")
        current_rejection={"round":rejection_data.get("round"),"issues":notes,"output_sha256":source_sha,
                           "archived_output":str(archived.relative_to(ROOT))}
        by_id[card_id]={**record,"slug":previous["slug"],"input_contract_version":1,
          "visual_descriptor_version":2,"render_contract_version":RENDER_CONTRACT_VERSION,
          "visual_benchmark_version":VISUAL_BENCHMARK_VERSION,"generation_mode":"native Gemini full-face fix",
          "source_rejection":current_rejection,
          "fix_history":[*previous.get("fix_history",[]),current_rejection],
          "card_json":str(card_path.relative_to(ROOT)),"card_sha256":sha(card_path),
          "prompt":str(prompt_path.relative_to(ROOT)),"prompt_sha256":sha(prompt_path),
          "request":str(request_path.relative_to(ROOT)),"request_sha256":sha(request_path),
          "output":str(output.relative_to(ROOT)),"output_sha256":sha(output),
          "generation":str(output.with_name("generation.json").relative_to(ROOT)),
          "generated_at":datetime.now(timezone.utc).isoformat(),"qa_status":"pending_human_review"}
        updated={**manifest,"active_render_contract_version":RENDER_CONTRACT_VERSION,
          "records":[by_id[key] for key in sorted(by_id)]}
        manifest_path.write_text(json.dumps(updated,ensure_ascii=False,indent=2)+"\n")
        manifest=updated
    print(json.dumps({"status":"FIXED","records":len(rejected),"ids":sorted(rejected)},indent=2))

def validate():
    records=source_records()
    for record in records: validate_projection(ROOT,CONTRACT,record)
    print(json.dumps({"status":"PASS","contract_version":1,"records":len(records),
      "canonical_fields_verified":len(records)*len(CONTRACT["authoritative_fields"]),"visual_descriptor_version":2,
      "human_review_required":True},indent=2))

def validate_complete_set():
    """Validate every current bundle, provenance edge, QA hash, and released montage."""
    errors=[]
    def require(condition,message):
        if not condition: errors.append(message)
    manifest_path=OUT/"provenance.json"
    require(manifest_path.is_file(),"missing provenance manifest")
    manifest=json.loads(manifest_path.read_text()) if manifest_path.is_file() else {"records":[]}
    records=manifest.get("records",[]); canonical={item["id"]:item for item in source_records()}
    by_id={item.get("id"):item for item in records}
    require(len(records)==60,"provenance must contain exactly 60 records")
    require(set(by_id)==set(canonical),"provenance ids must be exactly 1 through 60")
    require(manifest.get("model")==image_model(),"manifest model does not match configured image model")
    require(manifest.get("schedule_enabled") is False,"generation schedule must remain disabled")
    counts={(kind,rarity):0 for kind in TYPES for rarity in RARITIES}; digests=[]
    for card_id,expected in canonical.items():
        record=by_id.get(card_id)
        if not record: continue
        for key in ("type","rarity","variant","word","canonical_source","authoritative_content"):
            require(record.get(key)==expected.get(key),f"card {card_id:03d} canonical {key} drift")
        counts[(expected["type"],expected["rarity"])]+=1
        require(valid_previous_record(record),f"card {card_id:03d} current bundle hash mismatch")
        try:
            card_path=ROOT/record["card_json"]; request_path=ROOT/record["request"]
            output_path=ROOT/record["output"]; generation_path=ROOT/record["generation"]
            card=json.loads(card_path.read_text()); request=json.loads(request_path.read_text())
            generation=json.loads(generation_path.read_text())
            require(card.get("content")==card_data(expected)["content"],f"card {card_id:03d} card.json content drift")
            require(request.get("model")==image_model(),f"card {card_id:03d} request model drift")
            require(request.get("workflow") in ("hypertext.gemini.style.generate_with_styles","hypertext.gemini.style.generate_with_styles/fix_mode"),
                    f"card {card_id:03d} request is not the native Gemini style workflow")
            require(request.get("target_type")==expected["type"] and request.get("target_rarity")==expected["rarity"],
                    f"card {card_id:03d} request target drift")
            reference_paths=[]
            for reference in request.get("references",[]):
                reference_path=ROOT/reference["path"]; reference_paths.append(reference_path)
                require(reference_path.is_file() and sha(reference_path)==reference.get("sha256"),
                        f"card {card_id:03d} reference hash mismatch: {reference.get('path')}")
            require(VISUAL_BENCHMARK in reference_paths,f"card {card_id:03d} omits locked SEE-v4 reference")
            require(generation_path.is_file() and generation.get("status")=="success",f"card {card_id:03d} generation metadata is not successful")
            require(generation.get("model")==image_model(),f"card {card_id:03d} generation model drift")
            require((generation.get("width"),generation.get("height"))==(1024,1536),f"card {card_id:03d} generation dimensions drift")
            with Image.open(output_path) as opened:
                require(opened.size==(1024,1536) and opened.format=="PNG",f"card {card_id:03d} raster is not 1024x1536 PNG")
            for repair in record.get("fix_history",[]):
                archived=ROOT/repair["archived_output"]
                require(archived.is_file() and sha(archived)==repair.get("output_sha256"),
                        f"card {card_id:03d} repair archive hash mismatch: {repair.get('archived_output')}")
            for regeneration in record.get("regeneration_history",[]):
                archived=ROOT/regeneration["archived_output"]
                require(archived.is_file() and sha(archived)==regeneration.get("source_output_sha256"),
                        f"card {card_id:03d} regeneration archive hash mismatch: {regeneration.get('archived_output')}")
            digests.append(record["output_sha256"])
        except (KeyError,OSError,ValueError,json.JSONDecodeError) as exc:
            errors.append(f"card {card_id:03d} bundle could not be validated: {exc}")
    require(all(value==3 for value in counts.values()),"each type/rarity cell must contain exactly three cards")
    require(len(digests)==len(set(digests))==60,"all 60 output rasters must have unique hashes")
    if QA.is_file():
        report=json.loads(QA.read_text())
        require(report.get("status")=="PASS" and not report.get("blocked_cards"),"final visual QA is not PASS")
        require(report.get("montage_released") is True,"final montage is not released")
        require(report.get("montage_visual_review",{}).get("status")=="PASS","final montage lacks a PASS visual review")
        montage=report.get("montage",{}); montage_path=ROOT/montage.get("path","")
        require(montage_path.is_file() and sha(montage_path)==montage.get("sha256"),"final montage hash mismatch")
        cards={item["id"]:item for item in report.get("cards",[])}
        require(len(cards)==60 and all(cards.get(item["id"],{}).get("output_sha256")==item.get("output_sha256")
                                      and cards[item["id"]].get("status")=="PASS" for item in records),
                "visual QA card hashes do not match the current set")
    else:
        errors.append("missing final visual QA report")
    if REJECTIONS.is_file():
        disposition=json.loads(REJECTIONS.read_text())
        require(disposition.get("status")=="PASS" and not disposition.get("blocked_cards")
                and not disposition.get("rejections"),"final visual disposition is not zero-blocker PASS")
        require(disposition.get("accepted_ids")==list(range(1,61)),"final visual disposition does not accept all 60 ids")
        require(disposition.get("montage_released") is True
                and disposition.get("montage_visual_review")=="PASS","final visual disposition lacks montage acceptance")
    else:
        errors.append("missing final visual disposition")
    validation={"requirement":"REQ-PPAUG-029","validated_at":datetime.now(timezone.utc).isoformat(),
      "status":"PASS" if not errors else "FAIL","records":len(records),"unique_output_hashes":len(set(digests)),
      "type_rarity_counts":{f"{kind}/{rarity}":counts[(kind,rarity)] for kind in TYPES for rarity in RARITIES},
      "checks":{"canonical_projection":not any("canonical" in error for error in errors),
                "bundle_and_reference_hashes":not any("hash" in error for error in errors),
                "native_generation_metadata":not any("generation" in error or "workflow" in error for error in errors),
                "image_dimensions_and_uniqueness":not any("raster" in error or "unique" in error for error in errors),
                "human_review_and_montage":not any("QA" in error or "montage" in error for error in errors)},
      "errors":errors}
    VALIDATION.write_text(json.dumps(validation,ensure_ascii=False,indent=2)+"\n")
    if errors: raise RuntimeError("complete-set validation failed: "+"; ".join(errors))
    print(json.dumps(validation,ensure_ascii=False,indent=2))

def reindex_existing():
    """Recover only self-consistent SEE-v4 bundles after an interrupted run."""
    by_id={}
    for record in source_records():
        slug=f"{record['id']:03d}-{record['type']}-{record['rarity']}-v{record['variant']}"
        case=OUT/"individual"/slug; output=case/"outputs/card_1024x1536.png"
        card_path=case/"card.json"; prompt_path=case/"prompt.txt"; request_path=case/"request.json"
        generation_path=output.with_name("generation.json")
        if not all(path.is_file() for path in (card_path,prompt_path,request_path,output,generation_path)):
            continue
        try:
            card=json.loads(card_path.read_text()); request=json.loads(request_path.read_text())
            generation=json.loads(generation_path.read_text())
        except (OSError,json.JSONDecodeError):
            continue
        expected=card_data(record)["content"]
        if (card.get("content")!=expected or request.get("input_contract_version")!=1
                or request.get("visual_descriptor_version")!=2
                or request.get("visual_benchmark_version")!=VISUAL_BENCHMARK_VERSION
                or request.get("canonical_source")!=record["canonical_source"]
                or generation.get("status")!="success" or generation.get("model")!=image_model()
                or generation.get("width")!=1024 or generation.get("height")!=1536):
            continue
        render_version=request.get("render_contract_version",2)
        if render_version not in SUPPORTED_RENDER_CONTRACT_VERSIONS:
            continue
        by_id[record["id"]]={**record,"slug":slug,"input_contract_version":1,
          "visual_descriptor_version":2,"render_contract_version":render_version,
          "visual_benchmark_version":VISUAL_BENCHMARK_VERSION,
          "card_json":str(card_path.relative_to(ROOT)),"card_sha256":sha(card_path),
          "prompt":str(prompt_path.relative_to(ROOT)),"prompt_sha256":sha(prompt_path),
          "request":str(request_path.relative_to(ROOT)),"request_sha256":sha(request_path),
          "output":str(output.relative_to(ROOT)),"output_sha256":sha(output),
          "generation":str(generation_path.relative_to(ROOT)),
          "generated_at":datetime.fromtimestamp(output.stat().st_mtime,timezone.utc).isoformat(),
          "provenance_origin":"reindexed self-consistent interrupted-run bundle",
          "qa_status":"pending_human_review"}
    manifest={"requirement":"REQ-PPAUG-029","input_contract_version":1,"visual_descriptor_version":2,
      "active_render_contract_version":RENDER_CONTRACT_VERSION,
      "visual_benchmark_version":VISUAL_BENCHMARK_VERSION,"visual_benchmark":str(VISUAL_BENCHMARK.relative_to(ROOT)),
      "method":"build_prompt_text -> hypertext.gemini.style.generate_with_styles","model":image_model(),
      "request":{"aspect_ratio":"2:3","image_size":"2K","response_modalities":["IMAGE"]},
      "visible_face_composition":"Gemini full-card raster only; no programmatic face drawing or overlays",
      "schedule_enabled":False,"human_review_required":True,"records":[by_id[k] for k in sorted(by_id)]}
    (OUT/"provenance.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":"REINDEXED","records":len(by_id),"ids":sorted(by_id)},indent=2))

def record_review_pass():
    """Record the completed full-resolution human review against current hashes."""
    manifest_path=OUT/"provenance.json"; manifest=json.loads(manifest_path.read_text()); records=manifest["records"]
    if len(records)!=60 or any(not valid_previous_record(record) for record in records):
        raise RuntimeError("human review may be recorded only for 60 hash-valid current cards")
    reviewed_at=datetime.now(timezone.utc).isoformat()
    report={"requirement":"REQ-PPAUG-029","round":"final","status":"PASS","reviewed_at":reviewed_at,
      "reviewer":"cap_alpha","method":"full-resolution individual faces via labeled type-by-rarity review sheets; montage release and inspection are recorded separately",
      "locked_benchmark":{"path":str(VISUAL_BENCHMARK.relative_to(ROOT)),"sha256":sha(VISUAL_BENCHMARK)},
      "checks":{"all_60_individual_faces_reviewed":True,"canonical_text_and_punctuation_visible":True,
        "literal_reference_bullets_visible":True,"compact_two_column_languages":True,
        "type_badges_icons_and_stats":True,"rarity_and_cost_geometry":True,
        "symbolic_art_without_recognizable_faces":True,"no_placeholders_or_stale_faces":True},
      "blocked_cards":[],"montage_released":False,
      "cards":[{"id":record["id"],"word":record["word"],"type":record["type"],"rarity":record["rarity"],
                "output_sha256":record["output_sha256"],"status":"PASS"} for record in records]}
    QA.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    for record in records: record["qa_status"]="accepted_human_review"; record["qa_reviewed_at"]=reviewed_at
    manifest["records"]=records; manifest["human_review_required"]=False
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":"PASS","reviewed_records":len(records)},indent=2))

def accepted_qa(records):
    if not QA.is_file(): raise RuntimeError("montage requires final visual QA evidence")
    report=json.loads(QA.read_text()); cards={item["id"]:item for item in report.get("cards",[])}
    if (report.get("status")!="PASS" or len(cards)!=60 or report.get("blocked_cards")
            or any(record.get("qa_status")!="accepted_human_review"
                   or cards.get(record["id"],{}).get("status")!="PASS"
                   or cards.get(record["id"],{}).get("output_sha256")!=record["output_sha256"] for record in records)):
        raise RuntimeError("montage is blocked until all 60 current output hashes pass visual QA")
    return report

def montage():
    records=json.loads((OUT/"provenance.json").read_text())["records"]
    if (len(records)!=60 or any(r.get("input_contract_version")!=1
                               or r.get("visual_descriptor_version")!=2
                               or r.get("visual_benchmark_version")!=VISUAL_BENCHMARK_VERSION
                               or r.get("render_contract_version") not in SUPPORTED_RENDER_CONTRACT_VERSIONS
                               or not valid_previous_record(r) for r in records)):
        raise RuntimeError("montage requires 60 hash-verified semantic-v1 / visual-v2 / SEE-v4 cards")
    report=accepted_qa(records)
    thumb=(212,316); label_h=32; margin=20; canvas=Image.new("RGB",(margin*2+12*thumb[0],margin*2+5*(thumb[1]+label_h)),"#111628")
    draw=ImageDraw.Draw(canvas); font=ImageFont.load_default(size=14)
    for row,kind in enumerate(TYPES):
      for col,record in enumerate(x for x in records if x["type"]==kind):
        x=margin+col*thumb[0]; y=margin+row*(thumb[1]+label_h); image=Image.open(ROOT/record["output"]).convert("RGB"); image.thumbnail(thumb,Image.Resampling.LANCZOS)
        canvas.paste(image,(x+(thumb[0]-image.width)//2,y)); draw.text((x+4,y+thumb[1]+7),f"{record['id']:03d} {kind.upper()} {record['rarity'].upper()} V{record['variant']}",fill="#eedcae",font=font)
    montage_path=OUT/"review-montage-by-type-rarity.png"; canvas.save(montage_path)
    report["montage_released"]=True; report["montage"]={"path":str(montage_path.relative_to(ROOT)),"sha256":sha(montage_path)}
    QA.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")

def record_montage_pass():
    """Bind the completed visual montage inspection to the released montage hash."""
    records=json.loads((OUT/"provenance.json").read_text())["records"]
    report=accepted_qa(records); montage=report.get("montage",{}); montage_path=ROOT/montage.get("path","")
    if not report.get("montage_released") or not montage_path.is_file() or sha(montage_path)!=montage.get("sha256"):
        raise RuntimeError("montage visual review requires the current released montage")
    report["montage_visual_review"]={"status":"PASS","reviewer":"cap_alpha","reviewed_at":datetime.now(timezone.utc).isoformat(),
      "sha256":montage["sha256"],"checks":{"all_60_current_faces_present":True,"labels_readable":True,
      "no_placeholders_or_stale_rejections":True,"no_semantic_drift_or_missing_separators":True,
      "no_recognizable_faces_or_portrait_likenesses":True}}
    QA.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":"PASS","montage_sha256":montage["sha256"]},indent=2))

def review_sheets():
    records=json.loads((OUT/"provenance.json").read_text())["records"]
    if (len(records)!=60 or any(r.get("input_contract_version")!=1
                               or r.get("visual_descriptor_version")!=2
                               or r.get("visual_benchmark_version")!=VISUAL_BENCHMARK_VERSION
                               or r.get("render_contract_version") not in SUPPORTED_RENDER_CONTRACT_VERSIONS
                               or not valid_previous_record(r) for r in records)):
        raise RuntimeError("review sheets require 60 hash-verified semantic-v1 / visual-v2 / SEE-v4 cards")
    target=OUT/"review-sheets"; target.mkdir(parents=True,exist_ok=True)
    font=ImageFont.load_default(size=24); label_h=56
    for kind in TYPES:
      for rarity in RARITIES:
        group=sorted((r for r in records if r["type"]==kind and r["rarity"]==rarity),key=lambda r:r["variant"])
        if len(group)!=3: raise RuntimeError(f"expected 3 cards for {kind}/{rarity}, found {len(group)}")
        canvas=Image.new("RGB",(3*1024,1536+label_h),"#111628"); draw=ImageDraw.Draw(canvas)
        for index,record in enumerate(group):
          with Image.open(ROOT/record["output"]) as opened: image=opened.convert("RGB")
          if image.size!=(1024,1536): raise RuntimeError(f"unexpected dimensions for card {record['id']}: {image.size}")
          x=index*1024; canvas.paste(image,(x,0))
          draw.text((x+20,1548),f"#{record['id']:03d} {record['word']} | {kind.upper()} / {rarity.upper()}",fill="#eedcae",font=font)
        canvas.save(target/f"{kind}-{rarity}.png")

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--generate",action="store_true"); parser.add_argument("--ids",help="comma-separated affected ids; default all")
    parser.add_argument("--force",action="store_true",help="archive and replace existing outputs"); parser.add_argument("--fix-rejected",action="store_true")
    parser.add_argument("--validate",action="store_true"); parser.add_argument("--reindex-existing",action="store_true")
    parser.add_argument("--record-review-pass",action="store_true"); parser.add_argument("--montage",action="store_true"); parser.add_argument("--record-montage-pass",action="store_true")
    parser.add_argument("--review-sheets",action="store_true"); parser.add_argument("--validate-set",action="store_true"); args=parser.parse_args()
    ids={int(x) for x in args.ids.split(",")} if args.ids else set()
    if args.validate: validate()
    if args.reindex_existing: reindex_existing()
    if args.generate: generate(ids,args.force)
    if args.fix_rejected: fix_rejected(ids)
    if args.record_review_pass: record_review_pass()
    if args.montage: montage()
    if args.record_montage_pass: record_montage_pass()
    if args.review_sheets: review_sheets()
    if args.validate_set: validate_complete_set()
    if not (args.validate or args.reindex_existing or args.generate or args.fix_rejected or args.record_review_pass or args.montage or args.record_montage_pass or args.review_sheets or args.validate_set):
        parser.error("choose --validate, --validate-set, --reindex-existing, --generate, --fix-rejected, --record-review-pass, --montage, --record-montage-pass, and/or --review-sheets")
if __name__=="__main__": main()
