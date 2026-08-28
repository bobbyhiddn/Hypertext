"""Answer the operator-driven text spool (HYPERTEXT_TEXT_DRIVER_DIR) from a designs module.

Usage: driver_daemon.py <designs_module.py> <spool_dir>
The module exposes DESIGNS[word] = (rarity, seed, candidate), META[word], and critic_json(word).
Stages are detected from each prompt's first line; the word from 'Word: X'. Unknown words are left for a human.
"""
import importlib.util, json, re, sys, time
from pathlib import Path

mod_path, spool = Path(sys.argv[1]), Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("designs", mod_path)
designs = importlib.util.module_from_spec(spec); spec.loader.exec_module(designs)

def stage_of(text):
    head = text[:200]
    if head.startswith("Derive the semantic identity"): return "seed"
    if head.startswith("Turn the already-derived semantic seed"): return "candidate"
    if head.startswith("You are the independent Hypertext ability critic"): return "critic"
    if head.startswith("You are generating research-backed metadata"): return "metadata"
    return None

def word_of(text):
    m = re.search(r"^Word:\s*([A-Z][A-Z' -]*)$", text, re.M)
    return m.group(1).strip() if m else None

def respond(stage, word):
    rarity, seed, cand = designs.DESIGNS[word]
    if stage == "seed": return seed
    if stage == "candidate": return cand
    if stage == "critic": return designs.critic_json(word)
    meta = dict(designs.META[word]); meta["ability_text"] = cand["ability_text"]; return meta

print(f"[daemon] watching {spool} for {sorted(designs.DESIGNS)}", flush=True)
while True:
    for prompt in sorted(spool.glob("*-prompt.txt")):
        resp = prompt.with_name(prompt.name.replace("-prompt.txt", "-response.txt"))
        if resp.exists(): continue
        text = prompt.read_text(encoding="utf-8")
        stage, word = stage_of(text), word_of(text)
        if not stage or word not in designs.DESIGNS:
            print(f"[daemon] SKIP {prompt.name}: stage={stage} word={word}", flush=True); continue
        resp.write_text(json.dumps(respond(stage, word), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[daemon] answered {prompt.name}: {word} {stage}", flush=True)
    time.sleep(2)
