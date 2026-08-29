"""Apply a designs module to card directories that already exist - a re-plan in place.

The plan phase picks its slot from the queue, so it cannot target card #023. A
redesign or a promotion needs the same deterministic gates run against a fixed
slot, with the content taken from a designs module instead of from the model.

    replan.py <designs_module.py> [--series series/2026-Q1] [--dry-run]

Every word in the module must already have a card directory in the series (the
directory keeps its number and slug; the printed rarity may change). The gates
are exactly the plan phase's: ability candidate validation, word weight, stats,
one lemma, ability shape, and the art rule. Nothing is written unless every
card passes, so a module is applied whole or not at all.

Afterwards run `REGEN=1 scripts/pipeline/selfheal.sh <slug>...` to rebuild the
prompt from the new card.json and render.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import yaml

from hypertext.cards.abilities import validate_ability_candidate
from hypertext.cards.ability_shape import load_series_abilities, shape_conflicts
from hypertext.cards.art_motifs import check_art_prompt, load_art_standards
from hypertext.cards.lemma_uniqueness import lemma_conflicts, load_series_records, summarize
from hypertext.cards.word_weight import check_word_weight
from hypertext.pipeline.daily import _validate_card_stats


def load_module(path: str):
    spec = importlib.util.spec_from_file_location("designs", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def card_dirs_by_word(series: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for p in sorted(series.glob("cards/*/card.json")):
        try:
            out[str(json.loads(p.read_text(encoding="utf-8"))["content"]["WORD"]).upper()] = p.parent
        except (OSError, ValueError, KeyError):
            continue
    return out


def build(word: str, mod, series: Path, card_dir: Path) -> tuple[dict, dict, list[str]]:
    """Return (card, meta, issues) for one word without writing anything."""
    rarity, seed, cand = mod.DESIGNS[word]
    meta_in = mod.META[word]
    card_type = str(getattr(mod, "TYPES", {})[word]).upper()
    number = int(card_dir.name[:3])
    issues: list[str] = []

    v = validate_ability_candidate(cand, seed, rarity)
    issues += [f"ability: {i}" for i in v.get("issues", [])]

    weight, weight_rationale = meta_in["weight"], meta_in["weight_rationale"]
    issues += [f"weight: {i}" for i in check_word_weight(weight, rarity, weight_rationale)]

    try:
        _validate_card_stats(meta_in["stats"], rarity, meta_in["stats_rationale"], word=word, weight=weight, series_dir=series)
    except RuntimeError as exc:
        issues.append(f"stats: {exc}")

    hebrew, greek = meta_in["hebrew"], meta_in["greek"]
    others = [r for r in load_series_records(series) if not r[0].startswith(f"{number:03d}-")]
    conflicts = lemma_conflicts(
        {"WORD": word, "CARD_TYPE": card_type, "HEBREW": hebrew["text"], "HEBREW_TRANSLIT": hebrew["translit"], "GREEK": greek["text"]},
        others,
    )
    if conflicts:
        issues.append("lemma: " + summarize(conflicts))

    ability_text = cand["ability_text"]
    shape = shape_conflicts(ability_text, [r for r in load_series_abilities(series) if not r[0].startswith(f"{number:03d}-")])
    if shape:
        issues.append("shape: same shape as " + ", ".join(f"{c['with']}" for c in shape))

    art_prompt = meta_in["art_prompt"]
    issues += [f"art: {i}" for i in check_art_prompt(word, art_prompt, load_art_standards(series))]

    card = json.loads((card_dir / "card.json").read_text(encoding="utf-8"))
    c = card["content"]
    ot, nt = meta_in["ot_verse"], meta_in["nt_verse"]
    c.update({
        "WORD": word,
        "GLOSS": meta_in["gloss"],
        "CARD_TYPE": card_type,
        "RARITY_TEXT": rarity,
        "RARITY_ICON": rarity,
        "ART_PROMPT": art_prompt,
        "ABILITY_TEXT": ability_text,
        "STAT_LORE": int(meta_in["stats"]["lore"]),
        "STAT_CONTEXT": int(meta_in["stats"]["context"]),
        "STAT_COMPLEXITY": int(meta_in["stats"]["complexity"]),
        "OT_VERSE_REF": ot["ref"],
        "OT_VERSE_SNIPPET": ot["snippet"],
        "NT_VERSE_REF": nt["ref"],
        "NT_VERSE_SNIPPET": nt["snippet"],
        "OT_VERSE_LINE": f"{ot['ref']} — “{ot['snippet']}”",
        "NT_VERSE_LINE": f"{nt['ref']} — “{nt['snippet']}”",
        "GREEK": greek["text"],
        "GREEK_TRANSLIT": greek["translit"],
        "HEBREW": hebrew["text"],
        "HEBREW_TRANSLIT": hebrew["translit"],
        "OT_REFS": meta_in["ot_refs"],
        "NT_REFS": meta_in["nt_refs"],
        "TRIVIA_BULLETS": [str(x).strip() for x in meta_in["trivia"] if str(x).strip()],
    })

    old_meta = {}
    meta_path = card_dir / "meta.yml"
    if meta_path.exists():
        old_meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
    meta = dict(old_meta)
    meta.update({
        "number": f"{number:03d}",
        "word": word,
        "gloss": meta_in["gloss"],
        "card_type": card_type,
        "rarity": rarity,
        "art_prompt": art_prompt,
        "stats": {"lore": c["STAT_LORE"], "context": c["STAT_CONTEXT"], "complexity": c["STAT_COMPLEXITY"]},
        "stats_rationale": meta_in["stats_rationale"],
        "weight": int(weight),
        "weight_rationale": str(weight_rationale).strip(),
        "ability": ability_text,
        "ot_verse": {"ref": ot["ref"], "snippet": ot["snippet"]},
        "nt_verse": {"ref": nt["ref"], "snippet": nt["snippet"]},
        "greek": {"text": greek["text"], "translit": greek["translit"]},
        "hebrew": {"text": hebrew["text"], "translit": hebrew["translit"]},
        "ot_refs": meta_in["ot_refs"],
        "nt_refs": meta_in["nt_refs"],
        "trivia": c["TRIVIA_BULLETS"],
    })
    return card, meta, issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("module")
    ap.add_argument("--series", default="series/2026-Q1")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    series = Path(args.series)
    mod = load_module(args.module)
    dirs = card_dirs_by_word(series)

    missing = [w for w in mod.DESIGNS if w not in dirs]
    if missing:
        print(f"no existing card directory for: {', '.join(missing)}", file=sys.stderr)
        return 2

    planned, failed = [], 0
    for word in mod.DESIGNS:
        card_dir = dirs[word]
        card, meta, issues = build(word, mod, series, card_dir)
        rarity = mod.DESIGNS[word][0]
        if issues:
            failed += 1
            print(f"{card_dir.name:18s} {word:11s} {rarity:9s} FAIL")
            for i in issues:
                print(f"    {i}")
        else:
            print(f"{card_dir.name:18s} {word:11s} {rarity:9s} ok")
            planned.append((card_dir, card, meta))

    if failed:
        print(f"\n{failed} card(s) failed; nothing written")
        return 1
    if args.dry_run:
        print(f"\n{len(planned)} card(s) would be written (dry run)")
        return 0
    for card_dir, card, meta in planned:
        (card_dir / "card.json").write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (card_dir / "meta.yml").write_text(yaml.safe_dump(meta, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"\n{len(planned)} card(s) written; now run: REGEN=1 scripts/pipeline/selfheal.sh " + " ".join(d.name for d, _, _ in planned))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
