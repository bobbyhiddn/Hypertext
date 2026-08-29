"""Offline pre-flight for a designs module: run every deterministic set rule before spending a render.

Usage: offline_check.py <designs_module.py> [--exclude 001,002,...] [WORD:TYPE ...]
Slots listed in --exclude are dropped from the existing-set corpus, so a module that
replaces them is not reported as conflicting with the abilities it is replacing.
The module exposes DESIGNS[word] = (rarity, seed, candidate) and META[word]; card types come from a
TYPES = {word: type} dict in the module or from WORD:TYPE arguments. Exit 1 on any finding.
"""
import importlib.util, re, sys
from collections import Counter
from hypertext.cards.abilities import validate_ability_candidate, _estimate_printed_ratings, ABILITY_WORD_CAPS
from hypertext.cards.ability_shape import load_series_abilities, shape_conflicts, ability_signature, signature_key
from hypertext.cards.lemma_uniqueness import lemma_conflicts, load_series_records
from hypertext.cards.word_weight import check_word_weight
from hypertext.cards import ability_grammar as ag
from hypertext.cards import axes as ax
from hypertext.cards import art_motifs as am

SERIES = "series/2026-Q1"
WORD = re.compile(r"\b[\w'-]+\b")

def bucket(total):
    return 1 if total <= 10 else 2 if total <= 40 else 3 if total <= 120 else 4 if total <= 400 else 5

def main():
    spec = importlib.util.spec_from_file_location("designs", sys.argv[1])
    d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
    types = dict(getattr(d, "TYPES", {}))
    exclude: set[str] = set()
    args = sys.argv[2:]
    if args and args[0] == "--exclude":
        exclude = {x.strip() for x in args[1].split(",") if x.strip()}
        args = args[2:]
    for arg in args:
        w, t = arg.split(":"); types[w] = t
    missing = [w for w in d.DESIGNS if w not in types]
    if missing:
        sys.exit(f"no card type for {missing}: add TYPES to the module or pass WORD:TYPE")
    keep = lambda label: label.split("-")[0] not in exclude
    existing_ab = [r for r in load_series_abilities(SERIES) if keep(r[0])]
    existing_rec = [r for r in load_series_records(SERIES) if keep(r[0])]
    art = am.load_art_standards(SERIES)
    findings, sigs, batch_axes, batch_art = 0, {}, [], []
    for w, (rar, seed, cand) in d.DESIGNS.items():
        text, m = cand["ability_text"], d.META[w]
        print(f"\n=== {w} {types[w]} {rar}  words={len(WORD.findall(text))}/{ABILITY_WORD_CAPS[rar]}")
        r = validate_ability_candidate(cand, seed, rar)
        if r.get("issues"):
            findings += 1; print(" validate:", r["issues"])
        est = _estimate_printed_ratings(text, cand["rules_actions"])
        decl = {k: v["rating"] for k, v in cand["rarity_budget"].items()}
        if est != decl:
            findings += 1; print(" ratings differ from the estimator:", est, "vs declared", decl)
        own = f"-{w.lower()}"   # a design already planned into the series is not its own conflict
        sc = shape_conflicts(text, [r for r in existing_ab if not r[0].endswith(own)])
        if sc:
            findings += 1; print(" shape conflict:", sc)
        sigs[w] = signature_key(ability_signature(text))
        content = {"WORD": w, "CARD_TYPE": types[w], "HEBREW": m["hebrew"]["text"], "HEBREW_TRANSLIT": m["hebrew"]["translit"],
                   "GREEK": m["greek"]["text"], "GREEK_TRANSLIT": m["greek"]["translit"]}
        lc = lemma_conflicts(content, [r for r in existing_rec if not r[0].endswith(own)])
        if lc:
            findings += 1; print(" lemma conflict:", lc)
        ww = check_word_weight(m["weight"], rar, m["weight_rationale"])
        if ww:
            findings += 1; print(" weight:", ww)
        g = ag.classify(text)
        if g.get("unclassified"):
            findings += 1; print(" grammar: unclassified")
        else:
            print(" grammar:", {k: v for k, v in g.items() if v and k != "unclassified"})
        nums = [int(x) for x in re.findall(r"total (\d+)", m["stats_rationale"]["context"])]
        if not nums or bucket(nums[0]) != m["stats"]["context"]:
            findings += 1; print(f" CONTEXT: rationale total {nums} does not match declared bucket {m['stats']['context']}")
        if rar in ("COMMON", "UNCOMMON") and sum(1 for v in m["stats"].values() if v >= 4) >= 3:
            findings += 1; print(" STATS: three stats of 4+ on a", rar)
        # A heavy stat row must be earned by a heavy word (2026-08-29).
        row = sum(m["stats"].values())
        if row >= 13 and int(m["weight"]) < 4:
            findings += 1; print(f" STATS: total {row} needs word weight 4 or more; weight is {m['weight']}")
        # Numerals and function words cap CONTEXT (2026-08-29).
        capped = {str(x).upper() for x in ((am.yaml.safe_load(open(f"{SERIES}/set-standards.yml", encoding="utf-8")) or {}).get("stats") or {}).get("context_capped_words", [])}
        if w.upper() in capped and m["stats"]["context"] > 3:
            findings += 1; print(f" STATS: {w} is a numeral or function word; CONTEXT caps at 3")
        # Art: subject, figures, lighting clause (2026-08-29).
        art_issues = am.check_art_prompt(w, m["art_prompt"], art, tower_used=am.tower_count(SERIES, skip_word=w))
        if art_issues:
            findings += 1; print(" ART:", "; ".join(art_issues))
        batch_art.append((w.lower(), w, m["art_prompt"]))
        batch_axes.append(text)
        print(" axes:", ", ".join(sorted(ax.classify_axes(text))) or "none",
              "| lighting:", am.lighting_of(m["art_prompt"], art),
              "| motifs:", ", ".join(sorted(am.motifs_in(m["art_prompt"]))) or "none")
        print(" ok" if findings == 0 else "", sigs[w])
    dup = [k for k, v in Counter(sigs.values()).items() if v > 1]
    if dup:
        findings += 1; print("\nintra-batch duplicate shapes:", dup)
    # Mechanic axes: the batch must carry its share (2026-08-29).
    shortfalls = ax.batch_shortfalls(SERIES, batch_axes)
    if shortfalls:
        findings += len(shortfalls)
        print("\nmechanic axes:")
        for s in shortfalls:
            print("  " + s)
    # Art: how this batch moves the set against its caps.
    after = am.audit_series(SERIES, extra=batch_art)
    over = {**after["over_motif_caps"]}
    if over or after["over_lighting_cap"]:
        print("\nart caps after this batch:")
        for motif, n in over.items():
            print(f"  {motif}: {n} of {after['motif_caps'][motif]} allowed")
        for name, n in after["over_lighting_cap"].items():
            print(f"  lighting {name}: {n}/{after['cards']} over the {after['lighting_share_cap']:.0%} share cap")
        print("  (a legacy overrun is reported, not charged to this batch; a NEW overrun this batch causes is a finding)")
    # Lighting is reported, never charged: golden is the set's signature, and the
    # monotony worth fixing is in the subjects (towers, plains), not the light.
    print("\nbatch lighting:", dict(Counter(am.lighting_of(p, art) for _, _, p in batch_art)))
    print(f"\n{findings} finding(s)")
    sys.exit(1 if findings else 0)

if __name__ == "__main__":
    main()
