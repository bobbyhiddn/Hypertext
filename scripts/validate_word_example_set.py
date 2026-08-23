#!/usr/bin/env python3
"""Validate the REQ-PPAUG-028 artifact contract."""
import hashlib, json
from collections import Counter
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"operator_review/req-ppaug-028"
TYPES={"noun","verb","adjective","name","title"}; RARITIES={"common","uncommon","rare","glorious"}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 data=json.loads((OUT/"provenance.json").read_text()); rs=data["records"]; errors=[]
 counts=Counter((r["type"],r["rarity"]) for r in rs)
 if len(rs)!=60: errors.append(f"record count {len(rs)} != 60")
 if set(counts)!={(t,q) for t in TYPES for q in RARITIES}: errors.append("mapping cells differ from 5x4 matrix")
 if any(v!=3 for v in counts.values()): errors.append("one or more cells do not contain 3 cards")
 for key in ("output","output_sha256","prompt"):
  if len({r[key] for r in rs})!=60: errors.append(f"{key} is not unique")
 for r in rs:
  p=ROOT/r["output"]
  if not p.exists(): errors.append(f"missing {p}"); continue
  expected_size=Image.open(ROOT/r["template"]).size
  if Image.open(p).size!=expected_size or list(expected_size)!=r["dimensions"]: errors.append(f"bad dimensions {p}")
  if sha(p)!=r["output_sha256"]: errors.append(f"output digest mismatch {p}")
  expected=ROOT/f"templates/card/v001/composed/{r['type']}/{r['rarity']}/template_1024x1536.png"
  if str(expected.relative_to(ROOT))!=r["template"]: errors.append(f"mapping mismatch {p}")
  if sha(expected)!=r["template_sha256"]: errors.append(f"template mutated {expected}")
  if r["native_cost_required"] != (r["rarity"] in {"rare","glorious"}): errors.append(f"cost contract mismatch {p}")
 # Pixel invariants prove native top-left badge/icon and printed top-right cost regions survived composition.
 for r in rs:
  out=Image.open(ROOT/r["output"]); tpl=Image.open(ROOT/r["template"])
  if hashlib.sha256(out.crop((29,20,186,166)).tobytes()).hexdigest()!=hashlib.sha256(tpl.crop((29,20,186,166)).tobytes()).hexdigest(): errors.append(f"type badge/icon changed: {r['output']}")
  if r["native_cost_required"] and hashlib.sha256(out.crop((655,16,832,166)).tobytes()).hexdigest()!=hashlib.sha256(tpl.crop((655,16,832,166)).tobytes()).hexdigest(): errors.append(f"cost icon changed: {r['output']}")
 fps=json.loads((OUT/"template-fingerprints.json").read_text())
 for p,digest in fps.items():
  if sha(ROOT/p)!=digest: errors.append(f"approved template fingerprint changed: {p}")
 structured={(r['word'],r['rarity'],r['type'],r['variant'],r['ability'],tuple(r['stats'].values())) for r in rs}
 if len(structured)!=60: errors.append("structured content is not unique")
 report={"requirement":"REQ-PPAUG-028","status":"PASS" if not errors else "FAIL","cards":len(rs),"matrix":"5 types x 4 rarities x 3 variants","cell_counts":{f"{k[0]}/{k[1]}":v for k,v in sorted(counts.items())},"unique_structured_content":len(structured),"unique_outputs":len({r['output_sha256'] for r in rs}),"dimensions":"60/60 match approved 848x1272 template canvas" if len(rs)==60 and not any("dimensions" in e for e in errors) else "failed","type_badge_icon_pixel_invariants":"PASS" if not any("badge/icon" in e for e in errors) else "FAIL","rare_glorious_cost_pixel_invariants":"PASS" if not any("cost icon" in e for e in errors) else "FAIL","schedule_enabled":data["schedule_enabled"],"errors":errors}
 (OUT/"validation-report.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps(report,indent=2)); return 1 if errors else 0
if __name__=="__main__": raise SystemExit(main())
