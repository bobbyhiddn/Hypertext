#!/usr/bin/env python3
import argparse
import glob
import json
import os
import random
import subprocess
import sys
from pathlib import Path

from gemini_text import generate_text
from render_post import render_post

try:
    import yaml
except ImportError:
    yaml = None

DEFAULT_SERIES_DIR = Path("series/2026-Q1")
DEFAULT_TEMPLATE_PATH = Path("templates/card_prompt_template.json")
DEFAULT_DEMO_DIR = Path("series/2026-Q1/demo")


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


def _parse_json_from_model(text: str) -> dict:
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json\n", "", 1).replace("JSON\n", "", 1)
    return json.loads(raw)


def _generate_queue_entries(*, count: int, existing_words: list[str]) -> list[dict]:
    prompt = (
        "Generate "
        + str(count)
        + " distinct English words for a daily Biblical word-study trading card project. "
        "Avoid any words already used: "
        + ", ".join(existing_words)
        + ". "
        "For each item, choose: card_type (NOUN|VERB|ADJECTIVE|NAME|TITLE) and rarity (COMMON|UNCOMMON|RARE|MYTHIC). "
        "Return ONLY valid JSON as an array of objects with keys: word, card_type, rarity. "
        "word should be uppercase and A-Z only (no spaces)."
    )

    text = generate_text(prompt, model="gemini-3-pro-preview", temperature=0.7, use_google_search=False)
    data = _parse_json_from_model(text)
    if not isinstance(data, list):
        raise RuntimeError("Queue generation did not return a JSON array.")

    out: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        word = str(item.get("word", "")).strip().upper()
        card_type = str(item.get("card_type", "NOUN")).strip().upper()
        rarity = str(item.get("rarity", "COMMON")).strip().upper()
        if not word:
            continue
        out.append({"word": word, "card_type": card_type, "rarity": rarity})

    if len(out) != count:
        raise RuntimeError(f"Queue generation returned {len(out)} entries, expected {count}.")
    return out


def _generate_card_recipe(*, number: int, word: str, card_type: str, rarity: str) -> dict:
    prompt = (
        "You are generating research-backed metadata for a daily Bible word-study trading card. "
        "Return ONLY valid JSON with this exact shape: {\n"
        "  \"gloss\": string,\n"
        "  \"art_prompt\": string (must NOT mention text/letters/words/writing),\n"
        "  \"ability_text\": string,\n"
        "  \"stats\": {\"lore\": int 1-5, \"context\": int 1-5, \"complexity\": int 1-5},\n"
        "  \"ot_verse\": {\"ref\": string, \"snippet\": string},\n"
        "  \"nt_verse\": {\"ref\": string, \"snippet\": string},\n"
        "  \"greek\": {\"text\": string, \"translit\": string},\n"
        "  \"hebrew\": {\"text\": string, \"translit\": string},\n"
        "  \"ot_refs\": string (short refs separated by ' • '),\n"
        "  \"nt_refs\": string (short refs separated by ' • '),\n"
        "  \"trivia\": [3 to 5 strings]\n"
        "}.\n\n"
        f"Card number: {number:03d}\n"
        f"Word: {word}\n"
        f"Card type: {card_type}\n"
        f"Rarity: {rarity}\n\n"
        "Use Google Search grounding to pick appropriate verses and correct language forms. "
        "Verses/snippets must be short (not full verses). "
        "Keep ability_text consistent with rarity patterns (COMMON simple; UNCOMMON suit-based; RARE references stats; MYTHIC unique)."
    )

    text = generate_text(prompt, model="gemini-3-pro-preview", temperature=0.2, use_google_search=True)
    data = _parse_json_from_model(text)
    if not isinstance(data, dict):
        raise RuntimeError("Recipe generation did not return a JSON object.")
    return data


def _normalize_trivia(items: list[str]) -> list[str]:
    cleaned = [str(x).strip() for x in items if str(x).strip()]
    if len(cleaned) < 3:
        raise RuntimeError(f"Expected at least 3 trivia items, got {len(cleaned)}")
    if len(cleaned) > 5:
        cleaned = cleaned[:5]
    return cleaned


def _pick_demo_entry() -> dict:
    candidates = _generate_queue_entries(count=5, existing_words=[])
    return random.choice(candidates)


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


def phase_plan(*, series_dir: Path, template_path: Path, auto: bool) -> int:
    queue_path = series_dir / "deck" / "queue.yml"
    cards_dir = series_dir / "cards"

    print(f"Queue path: {queue_path}")
    queue = load_queue(queue_path)
    if auto:
        existing_words = [str(x.get("word", "")).upper() for x in queue if isinstance(x, dict)]
        min_queue = int(os.environ.get("HYPERTEXT_MIN_QUEUE", "3"))
        if len(queue) < min_queue:
            needed = min_queue - len(queue)
            print(f"Queue below minimum ({len(queue)}/{min_queue}). Generating {needed} new queue entries...")
            queue.extend(_generate_queue_entries(count=needed, existing_words=existing_words))
            save_queue(queue_path, queue)

    if not queue:
        print("Queue empty.")
        return 0


def phase_demo(*, series_dir: Path, template_path: Path, demo_dir: Path) -> int:
    if yaml is None:
        raise RuntimeError("pyyaml is required. Install with: pip install pyyaml")

    cards_dir = demo_dir / "cards"
    number = next_number(cards_dir)

    entry = _pick_demo_entry()
    word = str(entry["word"]).upper()
    slug = slugify(word)
    card_type = str(entry.get("card_type", "NOUN")).upper()
    rarity = str(entry.get("rarity", "COMMON")).upper()

    card_dir = cards_dir / f"{number:03d}-{slug}"
    os.makedirs(card_dir, exist_ok=True)

    if not template_path.exists():
        print(f"Missing {template_path}")
        return 1

    recipe = _generate_card_recipe(number=number, word=word, card_type=card_type, rarity=rarity)
    stats = recipe.get("stats", {}) if isinstance(recipe.get("stats"), dict) else {}
    ot_verse = recipe.get("ot_verse", {}) if isinstance(recipe.get("ot_verse"), dict) else {}
    nt_verse = recipe.get("nt_verse", {}) if isinstance(recipe.get("nt_verse"), dict) else {}
    greek = recipe.get("greek", {}) if isinstance(recipe.get("greek"), dict) else {}
    hebrew = recipe.get("hebrew", {}) if isinstance(recipe.get("hebrew"), dict) else {}

    trivia = recipe.get("trivia", [])
    if not isinstance(trivia, list):
        trivia = []
    trivia_items = _normalize_trivia([str(x) for x in trivia])

    gloss = str(recipe.get("gloss", "")).strip()
    art_prompt = str(recipe.get("art_prompt", "")).strip()
    ability_text = str(recipe.get("ability_text", "")).strip()

    ot_ref = str(ot_verse.get("ref", "")).strip()
    ot_snip = str(ot_verse.get("snippet", "")).strip()
    nt_ref = str(nt_verse.get("ref", "")).strip()
    nt_snip = str(nt_verse.get("snippet", "")).strip()

    card = read_json(template_path)
    card.setdefault("content", {})

    card["content"]["NUMBER"] = f"{number:03d}"
    card["content"]["WORD"] = word
    card["content"]["GLOSS"] = gloss
    card["content"]["CARD_TYPE"] = card_type
    card["content"]["RARITY_TEXT"] = rarity
    card["content"]["RARITY_ICON"] = rarity
    card["content"]["ART_PROMPT"] = art_prompt
    card["content"]["ABILITY_TEXT"] = ability_text

    card["content"]["STAT_LORE"] = int(stats.get("lore", 3))
    card["content"]["STAT_CONTEXT"] = int(stats.get("context", 3))
    card["content"]["STAT_COMPLEXITY"] = int(stats.get("complexity", 3))

    card["content"]["OT_VERSE_REF"] = ot_ref
    card["content"]["OT_VERSE_SNIPPET"] = ot_snip
    card["content"]["NT_VERSE_REF"] = nt_ref
    card["content"]["NT_VERSE_SNIPPET"] = nt_snip
    card["content"]["OT_VERSE_LINE"] = f"{ot_ref} — “{ot_snip}”"
    card["content"]["NT_VERSE_LINE"] = f"{nt_ref} — “{nt_snip}”"

    card["content"]["GREEK"] = str(greek.get("text", "")).strip()
    card["content"]["GREEK_TRANSLIT"] = str(greek.get("translit", "")).strip()
    card["content"]["HEBREW"] = str(hebrew.get("text", "")).strip()
    card["content"]["HEBREW_TRANSLIT"] = str(hebrew.get("translit", "")).strip()
    card["content"]["OT_REFS"] = str(recipe.get("ot_refs", "")).strip()
    card["content"]["NT_REFS"] = str(recipe.get("nt_refs", "")).strip()
    card["content"]["TRIVIA_BULLETS"] = trivia_items

    write_json(card_dir / "card.json", card)

    prompt_text = build_prompt_text(card)
    with open(card_dir / "prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt_text)

    meta = {
        "number": f"{number:03d}",
        "word": word,
        "gloss": gloss,
        "card_type": card_type,
        "rarity": rarity,
        "art_prompt": art_prompt,
        "stats": {
            "lore": card["content"]["STAT_LORE"],
            "context": card["content"]["STAT_CONTEXT"],
            "complexity": card["content"]["STAT_COMPLEXITY"],
        },
        "ability": ability_text,
        "ot_verse": {"ref": ot_ref, "snippet": ot_snip},
        "nt_verse": {"ref": nt_ref, "snippet": nt_snip},
        "greek": {"text": card["content"]["GREEK"], "translit": card["content"]["GREEK_TRANSLIT"]},
        "hebrew": {"text": card["content"]["HEBREW"], "translit": card["content"]["HEBREW_TRANSLIT"]},
        "ot_refs": card["content"]["OT_REFS"],
        "nt_refs": card["content"]["NT_REFS"],
        "trivia": trivia_items,
        "wild_id": None,
        "wild_counts_as": None,
        "quartet_id": None,
        "letter": None,
        "notes": None,
    }
    with open(card_dir / "meta.yml", "w", encoding="utf-8") as f:
        yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True)

    out_png = card_dir / "outputs" / "card_1024x1536.png"
    subprocess.check_call([sys.executable, str(Path("tools") / "gemini_image.py"), str(card_dir / "prompt.txt"), str(out_png)])

    render_post(
        str(card_dir / "post.md"),
        word=word,
        gloss=gloss,
        ot_ref=ot_ref,
        ot_snip=ot_snip,
        nt_ref=nt_ref,
        nt_snip=nt_snip,
        trivia_items=trivia_items,
        image_rel_path=f"./outputs/{out_png.name}",
    )

    print(f"Generated demo card at {card_dir}")
    return 0

    print(f"Queue entries: {len(queue)}")

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

    print(f"Template path: {template_path}")

    card = read_json(template_path)
    card.setdefault("content", {})

    card_type = str(entry.get("card_type", "NOUN")).upper()
    rarity = str(entry.get("rarity", "COMMON")).upper()

    if auto:
        recipe = _generate_card_recipe(number=number, word=word, card_type=card_type, rarity=rarity)
        stats = recipe.get("stats", {}) if isinstance(recipe.get("stats"), dict) else {}
        ot_verse = recipe.get("ot_verse", {}) if isinstance(recipe.get("ot_verse"), dict) else {}
        nt_verse = recipe.get("nt_verse", {}) if isinstance(recipe.get("nt_verse"), dict) else {}
        greek = recipe.get("greek", {}) if isinstance(recipe.get("greek"), dict) else {}
        hebrew = recipe.get("hebrew", {}) if isinstance(recipe.get("hebrew"), dict) else {}
        trivia = recipe.get("trivia", [])
        if not isinstance(trivia, list):
            trivia = []

        gloss = str(recipe.get("gloss", "")).strip()
        art_prompt = str(recipe.get("art_prompt", "")).strip()
        ability_text = str(recipe.get("ability_text", "")).strip()

        ot_ref = str(ot_verse.get("ref", "")).strip()
        ot_snip = str(ot_verse.get("snippet", "")).strip()
        nt_ref = str(nt_verse.get("ref", "")).strip()
        nt_snip = str(nt_verse.get("snippet", "")).strip()

        card["content"]["NUMBER"] = f"{number:03d}"
        card["content"]["WORD"] = word
        card["content"]["GLOSS"] = gloss
        card["content"]["CARD_TYPE"] = card_type
        card["content"]["RARITY_TEXT"] = rarity
        card["content"]["RARITY_ICON"] = rarity

        card["content"]["ART_PROMPT"] = art_prompt
        card["content"]["ABILITY_TEXT"] = ability_text

        card["content"]["STAT_LORE"] = int(stats.get("lore", 3))
        card["content"]["STAT_CONTEXT"] = int(stats.get("context", 3))
        card["content"]["STAT_COMPLEXITY"] = int(stats.get("complexity", 3))

        card["content"]["OT_VERSE_REF"] = ot_ref
        card["content"]["OT_VERSE_SNIPPET"] = ot_snip
        card["content"]["NT_VERSE_REF"] = nt_ref
        card["content"]["NT_VERSE_SNIPPET"] = nt_snip

        card["content"]["OT_VERSE_LINE"] = f"{ot_ref} — “{ot_snip}”"
        card["content"]["NT_VERSE_LINE"] = f"{nt_ref} — “{nt_snip}”"

        card["content"]["GREEK"] = str(greek.get("text", "")).strip()
        card["content"]["GREEK_TRANSLIT"] = str(greek.get("translit", "")).strip()
        card["content"]["HEBREW"] = str(hebrew.get("text", "")).strip()
        card["content"]["HEBREW_TRANSLIT"] = str(hebrew.get("translit", "")).strip()

        card["content"]["OT_REFS"] = str(recipe.get("ot_refs", "")).strip()
        card["content"]["NT_REFS"] = str(recipe.get("nt_refs", "")).strip()
        card["content"]["TRIVIA_BULLETS"] = [str(x).strip() for x in trivia if str(x).strip()]

        meta = {
            "number": f"{number:03d}",
            "word": word,
            "gloss": gloss,
            "card_type": card_type,
            "rarity": rarity,
            "art_prompt": art_prompt,
            "stats": {
                "lore": card["content"]["STAT_LORE"],
                "context": card["content"]["STAT_CONTEXT"],
                "complexity": card["content"]["STAT_COMPLEXITY"],
            },
            "ability": ability_text,
            "ot_verse": {"ref": ot_ref, "snippet": ot_snip},
            "nt_verse": {"ref": nt_ref, "snippet": nt_snip},
            "greek": {"text": card["content"]["GREEK"], "translit": card["content"]["GREEK_TRANSLIT"]},
            "hebrew": {"text": card["content"]["HEBREW"], "translit": card["content"]["HEBREW_TRANSLIT"]},
            "ot_refs": card["content"]["OT_REFS"],
            "nt_refs": card["content"]["NT_REFS"],
            "trivia": card["content"]["TRIVIA_BULLETS"],
            "wild_id": None,
            "wild_counts_as": None,
            "quartet_id": None,
            "letter": None,
            "notes": None,
        }

        with open(card_dir / "meta.yml", "w", encoding="utf-8") as f:
            yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True)
    else:
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
    for p in sorted(card_dir.rglob("*")):
        if p.is_file():
            print(f"  wrote: {p}")
    return 0


def phase_imagegen(*, series_dir: Path) -> int:
    cards_dir = series_dir / "cards"
    out_name = "card_1024x1536.png"

    print(f"Looking for card folders in: {cards_dir}")
    target_dir = find_next_image_target(cards_dir, out_name)
    if target_dir is None:
        latest = find_latest_card_dir(cards_dir)
        if latest is None:
            print("No cards found.")
            return 1
        print("No missing images found.")
        return 0

    prompt_file = target_dir / "prompt.txt"
    out_png = target_dir / "outputs" / out_name

    subprocess.check_call([sys.executable, str(Path("tools") / "gemini_image.py"), str(prompt_file), str(out_png)])

    print(f"Rendered image at {out_png}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["plan", "imagegen", "demo"], required=True)
    parser.add_argument("--series", default=str(DEFAULT_SERIES_DIR))
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE_PATH))
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--demo-dir", default=str(DEFAULT_DEMO_DIR))
    args = parser.parse_args()

    series_dir = Path(args.series)
    template_path = Path(args.template)

    if args.phase == "plan":
        return phase_plan(series_dir=series_dir, template_path=template_path, auto=args.auto)

    if args.phase == "imagegen":
        return phase_imagegen(series_dir=series_dir)

    if args.phase == "demo":
        return phase_demo(series_dir=series_dir, template_path=template_path, demo_dir=Path(args.demo_dir))

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
