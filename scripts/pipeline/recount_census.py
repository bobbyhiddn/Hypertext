"""Recompute schema/babel_template_matrix.json and series/<s>/stats.yml from the cards themselves.

batch_run.sh increments the census as it queues each new card, which is right for an
append-only batch and wrong the moment a card changes tier. The cards are the source of
truth, so this recounts them and reports every cell that moved, plus the distance from
the targets in set-standards.yml.

    recount_census.py [--series series/2026-Q1] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import yaml


def census(series: Path) -> Counter:
    counts: Counter = Counter()
    for p in sorted(series.glob("cards/*/card.json")):
        try:
            c = json.loads(p.read_text(encoding="utf-8"))["content"]
        except (OSError, ValueError, KeyError):
            continue
        counts[(str(c["CARD_TYPE"]).upper(), str(c["RARITY_TEXT"]).upper())] += 1
    return counts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", default="series/2026-Q1")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    series = Path(args.series)

    counts = census(series)
    matrix_path = Path("schema/babel_template_matrix.json")
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    moved = []
    for cell in matrix["valid_combinations"]:
        now = counts.get((cell["type"], cell["rarity"]), 0)
        if cell["card_count"] != now:
            moved.append(f"{cell['type']:9s} {cell['rarity']:9s} {cell['card_count']:2d} -> {now:2d}")
        cell["card_count"] = now
    matrix["totals"]["canonical_cards"] = sum(counts.values())

    standards = yaml.safe_load((series / "set-standards.yml").read_text(encoding="utf-8")) or {}
    targets = standards.get("combination_targets") or {}
    stats_path = series / "stats.yml"
    stats = yaml.safe_load(stats_path.read_text(encoding="utf-8")) or {}
    stats["rarity_counts"] = {r: sum(v for (t, rr), v in counts.items() if rr == r) for r in ("GLORIOUS", "RARE", "UNCOMMON", "COMMON")}
    stats["type_counts"] = {t: sum(v for (tt, r), v in counts.items() if tt == t) for t in ("NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE")}
    stats["combination_counts"] = {f"{r}_{t}": counts.get((t, r), 0) for (t, r) in sorted(counts, key=lambda k: (k[1], k[0]))}

    for line in moved:
        print(line)
    print(f"\n{sum(counts.values())} cards; rarities {dict(stats['rarity_counts'])}")
    open_slots = {k: targets[k] - counts.get((k.split('_', 1)[1], k.split('_', 1)[0]), 0) for k in targets}
    remaining = {k: v for k, v in open_slots.items() if v}
    print("open slots vs targets:", remaining or "none - the set is full")
    over = {k: v for k, v in remaining.items() if v < 0}
    if over:
        print("OVER TARGET:", over)

    if args.dry_run:
        print("(dry run; nothing written)")
        return 0
    matrix_path.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    stats_path.write_text(yaml.safe_dump(stats, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print("wrote schema/babel_template_matrix.json and", stats_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
