#!/usr/bin/env python3
import argparse
import glob
import json
import os
import subprocess
import sys
from pathlib import Path

from render_post import render_post

try:
    import yaml
except ImportError:
    yaml = None

DEFAULT_SERIES_DIR = Path("series/2026-Q1")
DEFAULT_TEMPLATE_PATH = Path("templates/card_prompt_template.json")


def slugify(word: str) -> str:
    out = []
    prev_dash = False
    for c in word.lower().strip():
        if c.isalnum():
            out.append(c)
            prev_dash = False
        else:
            if not prev_dash:
                out.append("-")
                prev_dash = True
    return "".join(out).strip("-")


def load_queue(queue_path: Path) -> list[dict]:
    if yaml is None:
        raise RuntimeError("pyyaml is required. Install with: pip install pyyaml")
    with open(queue_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or []


def save_queue(queue_path: Path, queue: list[dict]) -> None:
    if yaml is None:
        raise RuntimeError("pyyaml is required. Install with: pip install pyyaml")
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with open(queue_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(queue, f, sort_keys=False)


def next_number(cards_dir: Path) -> int:
    existing = sorted(glob.glob(str(cards_dir / "[0-9][0-9][0-9]-*")))
    if not existing:
        return 1
    last = os.path.basename(existing[-1]).split("-")[0]
    return int(last) + 1


def read_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def build_prompt_text(card: dict) -> str:
    recipe = card.get("model_prompt", "").strip()
    if not recipe:
        raise RuntimeError("card.json missing model_prompt")

    payload = json.dumps(card, ensure_ascii=False, indent=2)
    return f"{recipe}\n\nCARD_JSON:\n{payload}\n"


def find_latest_card_dir(cards_dir: Path) -> Path | None:
    dirs = sorted([Path(p) for p in glob.glob(str(cards_dir / "[0-9][0-9][0-9]-*"))])
    if not dirs:
        return None
    return dirs[-1]


def find_next_image_target(cards_dir: Path, out_name: str) -> Path | None:
    dirs = sorted([Path(p) for p in glob.glob(str(cards_dir / "[0-9][0-9][0-9]-*"))])
    for d in reversed(dirs):
        out_png = d / "outputs" / out_name
        prompt_txt = d / "prompt.txt"
        card_json = d / "card.json"
        if card_json.exists() and prompt_txt.exists() and not out_png.exists():
            return d
    return None


def phase_plan(*, series_dir: Path, template_path: Path) -> int:
    queue_path = series_dir / "deck" / "queue.yml"
    cards_dir = series_dir / "cards"

    queue = load_queue(queue_path)
    if not queue:
        print("Queue empty.")
        return 0

    entry = queue[0]

    number = next_number(cards_dir)
    word = str(entry["word"]).upper()
    slug = slugify(str(entry["word"]))
    card_dir = cards_dir / f"{number:03d}-{slug}"

    if card_dir.exists():
        print(f"Card dir already exists: {card_dir}")
        return 0

    if not template_path.exists():
        print(f"Missing {template_path}")
        return 1

    card = read_json(template_path)
    card.setdefault("content", {})

    card_type = str(entry.get("card_type", "NOUN")).upper()
    rarity = str(entry.get("rarity", "COMMON")).upper()

    card["content"]["NUMBER"] = f"{number:03d}"
    card["content"]["WORD"] = word
    card["content"]["GLOSS"] = "learned visitors from the East"
    card["content"]["CARD_TYPE"] = card_type

    card["content"]["RARITY_TEXT"] = rarity
    card["content"]["RARITY_ICON"] = rarity

    card["content"]["OT_VERSE_LINE"] = "Dan 2:2 — “summoned the magicians, enchanters, sorcerers, Chaldeans …”"
    card["content"]["NT_VERSE_LINE"] = "Matt 2:1 — “magi from the east came to Jerusalem …”"

    card["content"]["OT_VERSE_REF"] = "Daniel 2:2"
    card["content"]["OT_VERSE_SNIPPET"] = "summoned the magicians, enchanters, sorcerers, Chaldeans"
    card["content"]["NT_VERSE_REF"] = "Matthew 2:1"
    card["content"]["NT_VERSE_SNIPPET"] = "magi from the east came to Jerusalem"

    card["content"]["TRIVIA_BULLETS"] = [
        "Matthew never calls them kings, and never gives a number.",
        "The same Greek root appears in Acts 13:6 in a negative context.",
        "Daniel’s court vocabulary overlaps with ‘wise/magician’ categories.",
        "This label’s moral weight is decided by context, not the word alone.",
    ]

    card["content"]["ART_PROMPT"] = (
        "A moonlit caravan of eastern scholars approaching a distant city beneath a brilliant star; "
        "ancient Near Eastern travel; subtle wonder; parchment-friendly tones; no text in art"
    )

    card["content"]["ABILITY_TEXT"] = (
        "On draw, you may reveal: spend 1 card from your hand to activate that card’s on-reveal ability. "
        "Then this card is spent."
    )

    card["content"]["STAT_LORE"] = 5
    card["content"]["STAT_CONTEXT"] = 1
    card["content"]["STAT_COMPLEXITY"] = 3

    card["content"]["GREEK"] = "μάγος / μάγοι"
    card["content"]["GREEK_TRANSLIT"] = "magos / magoi"
    card["content"]["NT_REFS"] = "Matt 2:1 • Acts 13:6"
    card["content"]["HEBREW"] = "חרטמים / חכימין"
    card["content"]["HEBREW_TRANSLIT"] = "ḥarṭummîm / ḥăkîmîn"
    card["content"]["OT_REFS"] = "Dan 2:2 • Dan 4:7"

    write_json(card_dir / "card.json", card)

    prompt_text = build_prompt_text(card)
    with open(card_dir / "prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt_text)

    out_png = card_dir / "outputs" / "card_1024x1536.png"
    render_post(
        str(card_dir / "post.md"),
        word=word,
        gloss=card["content"]["GLOSS"],
        ot_ref=card["content"].get("OT_VERSE_REF", ""),
        ot_snip=card["content"].get("OT_VERSE_SNIPPET", ""),
        nt_ref=card["content"].get("NT_VERSE_REF", ""),
        nt_snip=card["content"].get("NT_VERSE_SNIPPET", ""),
        trivia_items=card["content"]["TRIVIA_BULLETS"],
        image_rel_path=f"./outputs/{out_png.name}",
    )

    save_queue(queue_path, queue[1:])

    print(f"Planned card at {card_dir}")
    return 0


def phase_imagegen(*, series_dir: Path) -> int:
    cards_dir = series_dir / "cards"
    out_name = "card_1024x1536.png"

    target_dir = find_next_image_target(cards_dir, out_name)
    if target_dir is None:
        latest = find_latest_card_dir(cards_dir)
        if latest is None:
            print("No cards found.")
            return 0
        print("No missing images found.")
        return 0

    prompt_file = target_dir / "prompt.txt"
    out_png = target_dir / "outputs" / out_name

    subprocess.check_call([sys.executable, str(Path("tools") / "gemini_image.py"), str(prompt_file), str(out_png)])

    print(f"Rendered image at {out_png}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["plan", "imagegen"], required=True)
    parser.add_argument("--series", default=str(DEFAULT_SERIES_DIR))
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE_PATH))
    args = parser.parse_args()

    series_dir = Path(args.series)
    template_path = Path(args.template)

    if args.phase == "plan":
        return phase_plan(series_dir=series_dir, template_path=template_path)

    if args.phase == "imagegen":
        return phase_imagegen(series_dir=series_dir)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
