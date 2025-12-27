#!/usr/bin/env python3
import argparse
import glob
import json
import os
import random
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from gemini_text import generate_text, generate_text_with_grounding
from gemini_review import (
    review_card,
    describe_card,
    score_against_rubric,
    format_review_report,
    format_description_report,
    ReviewResult,
    CardDescription,
)
from render_post import render_post

try:
    import yaml
except ImportError:
    yaml = None

DEFAULT_SERIES_DIR = Path("series/2026-Q1")
DEFAULT_TEMPLATE_PATH = Path("templates/card_prompt_template.json")
DEFAULT_DEMO_DIR = Path("demo_cards")
RULES_PATH = Path("docs/rules.md")

GAME_RULES_SNIPPET = (
    "- There is ONE shared 90-card deck. Do not say 'your deck'. Say 'the deck'.\n"
    "- The goal is to be the first to reach 20 points (if the deck runs out first, highest score wins).\n"
    "- Scoring: when a player completes a Quartet, they score 4 points and the completed Quartet is moved to the face-up discard pile.\n"
    "- There are no Season Goals or Personal Objectives.\n"
    "- The game ends immediately when a player reaches 20 points.\n"
    "- Abilities should be one short to medium line.\n"
    "- NEVER write abilities that just 'draw a card' - that's neutral tempo, not advantage. The ability must match the word in 'flavor'.\n"
    "- Abilities MUST provide card advantage (value beyond the card itself).\n"
    "- Rarity patterns: COMMON simple value; UNCOMMON type-based (NOUN/VERB/ADJECTIVE/NAME/TITLE); RARE stat-based(Must not reference its own stats); GLORIOUS unique/combo(Performs an action that is thematically consistent with the card's flavor, and does more than any other suit.)."
)

# Visual formatting standards that MUST be followed for card rendering
FORMATTING_RUBRIC = """
## CARD FORMATTING STANDARDS (must follow exactly)

### Card Number Format
- Format: #XXX (e.g., #001, #042)
- WRONG: [#001], 001, #1
- CORRECT: #001

### Stat Pips
- Shape: CIRCLES only (never diamonds, squares, or stars)
- Filled pip color: NAVY (dark blue, matching the card border)
- Empty pip color: Outlined circles with parchment fill
- WRONG: Gold-filled circles, yellow pips, diamond shapes
- CORRECT: Navy-blue solid filled circles for the stat value

### Rarity Icon
- Shape: DIAMOND for all rarities
- Position: Top right, after rarity text
- Colors by rarity:
  - COMMON: white diamond
  - UNCOMMON: green diamond
  - RARE: gold diamond
  - GLORIOUS: orange diamond
- Format: "RARE ◆" (text then icon, not "◆ RARE")

### Brackets
- NEVER use square brackets [ ] anywhere on the card
- WRONG: [NOUN], [#003], [RARE]
- CORRECT: NOUN, #003, RARE

### Text Display
- Greek text: Standard left-to-right display
- Hebrew text: Right-to-left display
- Transliteration: Show ONLY the transliterated word, no "transliteration:" prefix
- WRONG: "transliteration: diatheke" or "TRANSLIT: diatheke"
- CORRECT: "diathēkē"

### General
- Do NOT make changes beyond what was specifically requested
- Preserve existing correct formatting when making changes
- Only modify the specific fields mentioned in the revision request
"""


DEFAULT_STYLE_TEMPLATE = Path("tools") / "clean_template_final.png"
RARITY_ORDER = ["COMMON", "UNCOMMON", "RARE", "GLORIOUS"]
RARITY_TARGETS = {"COMMON": 40, "UNCOMMON": 35, "RARE": 15, "GLORIOUS": 10}


def _load_series_stats(series_dir: Path) -> dict:
    """Load series stats from stats.yml."""
    stats_path = series_dir / "stats.yml"
    if not stats_path.exists() or yaml is None:
        return {"counts": {r: 0 for r in RARITY_ORDER}, "total": 0, "targets": RARITY_TARGETS}
    
    with open(stats_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    
    counts = data.get("counts", {})
    for r in RARITY_ORDER:
        counts.setdefault(r, 0)
    
    return {
        "counts": counts,
        "total": data.get("total", sum(counts.values())),
        "targets": data.get("targets", RARITY_TARGETS),
    }


def _save_series_stats(series_dir: Path, stats: dict) -> None:
    """Save series stats to stats.yml."""
    if yaml is None:
        return
    stats_path = series_dir / "stats.yml"
    
    data = {
        "series": series_dir.name,
        "cycle_days": 90,
        "start_date": "2025-01-01",
        "targets": stats.get("targets", RARITY_TARGETS),
        "counts": stats["counts"],
        "total": stats["total"],
    }
    
    with open(stats_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def _get_needed_rarity(stats: dict) -> str:
    """Determine which rarity is most under-represented vs targets."""
    counts = stats["counts"]
    targets = stats.get("targets", RARITY_TARGETS)
    total = max(stats["total"], 1)
    
    # Calculate deficit: target% - current%
    deficits = {}
    for rarity in RARITY_ORDER:
        current_pct = (counts.get(rarity, 0) / total) * 100
        target_pct = targets.get(rarity, 25)
        deficits[rarity] = target_pct - current_pct
    
    # Return rarity with highest deficit
    return max(deficits, key=deficits.get)


def _find_card_by_rarity(series_root: Path) -> dict[str, Path]:
    """Find one card image per rarity from the series."""
    cards_dir = series_root / "cards"
    if not cards_dir.exists():
        return {}
    
    rarity_map: dict[str, Path] = {}
    for card_dir in sorted(cards_dir.iterdir()):
        if not card_dir.is_dir():
            continue
        meta_file = card_dir / "meta.yml"
        img_file = card_dir / "outputs" / "card_1024x1536.png"
        if not meta_file.exists() or not img_file.exists():
            continue
        
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("rarity:"):
                        rarity = line.split(":", 1)[1].strip().upper()
                        if rarity in RARITY_ORDER and rarity not in rarity_map:
                            rarity_map[rarity] = img_file
                        break
        except OSError:
            continue
    
    return rarity_map


def _build_style_refs(series_root: Path) -> tuple[list[str], dict[int, str]]:
    """Build list of style reference paths: template + one card per rarity.
    
    Returns:
        Tuple of (refs list, rarity_labels dict mapping 1-indexed position to rarity)
    """
    refs: list[str] = []
    rarity_labels: dict[int, str] = {}
    
    if DEFAULT_STYLE_TEMPLATE.exists():
        refs.append(str(DEFAULT_STYLE_TEMPLATE))
    
    rarity_map = _find_card_by_rarity(series_root)
    for rarity in RARITY_ORDER:
        if rarity in rarity_map:
            refs.append(str(rarity_map[rarity]))
            rarity_labels[len(refs)] = rarity  # 1-indexed position
    
    return refs, rarity_labels


def _build_style_cmd_args(
    style_refs: list[str],
    rarity_labels: dict[int, str] | None = None,
    target_rarity: str | None = None,
) -> list[str]:
    """Build CLI args for gemini_style.py from style ref list."""
    args: list[str] = []
    for ref in style_refs:
        args.extend(["--style", ref])
    
    if rarity_labels:
        for pos, rarity in rarity_labels.items():
            args.extend(["--rarity-label", f"{pos}:{rarity}"])
    
    if target_rarity:
        args.extend(["--target-rarity", target_rarity])
    
    return args


def _load_rules_appendix() -> str:
    try:
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            rules = f.read().strip()
    except OSError:
        rules = ""

    if not rules:
        return ""

    return "\n\nRULES (appendix; follow these exactly):\n" + rules


def _log(msg: str) -> None:
    print(msg, flush=True)


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
    if not raw:
        raise RuntimeError("Model returned empty response; expected JSON.")

    candidates: list[str] = [raw]
    if raw.startswith("```") and "```" in raw[3:]:
        parts = raw.split("```")
        if len(parts) >= 3:
            fenced = parts[1]
            fenced = fenced.lstrip()
            if fenced.lower().startswith("json"):
                fenced = fenced[4:]
            candidates.append(fenced.strip())

    decoder = json.JSONDecoder()
    last_err: Exception | None = None

    for cand in candidates:
        s = cand.strip()
        if not s:
            continue
        try:
            return json.loads(s)
        except Exception as e:
            last_err = e

        start_idx = None
        for ch in ("{", "["):
            i = s.find(ch)
            if i != -1 and (start_idx is None or i < start_idx):
                start_idx = i
        if start_idx is None:
            continue

        try:
            obj, _end = decoder.raw_decode(s[start_idx:])
            return obj
        except Exception as e:
            last_err = e

    snippet = raw[:400].replace("\n", "\\n")
    raise RuntimeError(f"Failed to parse JSON from model output. Snippet: {snippet}") from last_err


def _generate_queue_entries(*, count: int, existing_words: list[str], needed_rarities: list[str] | None = None) -> list[dict]:
    # Build rarity instruction based on what's needed
    if needed_rarities:
        rarity_instruction = (
            f"IMPORTANT: The series needs these rarities most urgently: {', '.join(needed_rarities)}. "
            f"Assign the FIRST entry rarity={needed_rarities[0]}. "
            "Distribute remaining entries to help balance the set."
        )
    else:
        rarity_instruction = (
            "IMPORTANT: Distribute rarities to form a balanced set "
            "(approx. 10% GLORIOUS, 15% RARE, 35% UNCOMMON, 40% COMMON)."
        )
    
    prompt = (
        "Generate "
        + str(count)
        + " distinct English words for a daily Biblical word-study trading card project. "
        "Avoid any words already used: "
        + ", ".join(existing_words)
        + ". "
        "For each item, choose: card_type (NOUN|VERB|ADJECTIVE|NAME|TITLE) and rarity (COMMON|UNCOMMON|RARE|GLORIOUS). "
        + rarity_instruction + " "
        "Return ONLY valid JSON as an array of objects with keys: word, card_type, rarity. "
        "word should be uppercase and A-Z only (no spaces)."
    )

    _log(f"[plan] generating queue entries (count={count})")
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


def _generate_card_recipe(*, number: int, word: str, card_type: str, rarity: str, ability: str | None = None) -> dict:
    rules_appendix = _load_rules_appendix()

    # If ability is provided, instruct the model to use it; otherwise generate one
    if ability:
        ability_instruction = (
            f"  \"ability_text\": \"{ability}\" (USE THIS EXACT ABILITY - do not modify),\n"
        )
        ability_note = f"ABILITY (use exactly as provided): {ability}\n\n"
    else:
        ability_instruction = "  \"ability_text\": string,\n"
        ability_note = ""

    prompt = (
        "You are generating research-backed metadata for a daily Bible word-study trading card. "
        "Return ONLY valid JSON with this exact shape: {\n"
        "  \"gloss\": string,\n"
        "  \"art_prompt\": string (must NOT mention text/letters/words/writing),\n"
        + ability_instruction +
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
        + ability_note +
        "GAME RULES (must follow):\n"
        + GAME_RULES_SNIPPET
        + rules_appendix
        + "\n\n"
        "Use Google Search grounding to pick appropriate verses and correct language forms. "
        "Verses/snippets must be short (not full verses). "
        + ("" if ability else "Keep ability_text consistent with rarity patterns (COMMON simple; UNCOMMON suit-based; RARE references stats; GLORIOUS unique).")
    )

    _log(f"[plan] generating recipe via Gemini (#{number:03d} {word} {card_type} {rarity})")
    text, grounding = generate_text_with_grounding(
        prompt,
        model="gemini-3-pro-preview",
        temperature=0.2,
        use_google_search=True,
    )
    try:
        data = _parse_json_from_model(text)
    except Exception:
        retry_prompt = prompt + "\n\nIMPORTANT: Return ONLY raw JSON (no markdown, no backticks, no commentary)."
        text, grounding = generate_text_with_grounding(
            retry_prompt,
            model="gemini-3-pro-preview",
            temperature=0.2,
            use_google_search=True,
        )
        data = _parse_json_from_model(text)
    if not isinstance(data, dict):
        raise RuntimeError("Recipe generation did not return a JSON object.")

    if isinstance(grounding, dict):
        data["grounding"] = grounding
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


def _read_text(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_revise_form(raw: str) -> tuple[str, set[str]]:
    def is_placeholder(s: str) -> bool:
        return "<" in s and ">" in s

    def is_empty_value(s: str) -> bool:
        if not s.strip():
            return True
        if s.strip() in ("-", "- -"):
            return True
        if is_placeholder(s.strip()):
            return True
        return False

    current_key: str | None = None
    rarity_lines: list[str] = []
    ability_lines: list[str] = []
    stats_lines: list[str] = []
    general_lines: list[str] = []

    for line in raw.splitlines():
        if line.lstrip().startswith("#"):
            continue

        if line.startswith("Rarity_Change_Request:"):
            current_key = "rarity"
            rest = line.split(":", 1)[1]
            if not is_empty_value(rest):
                rarity_lines.append(rest.strip())
            continue

        if line.startswith("Ability_Change_Request:"):
            current_key = "ability"
            rest = line.split(":", 1)[1]
            if not is_empty_value(rest):
                ability_lines.append(rest.strip())
            continue

        if line.startswith("Stats_Change_Request:"):
            current_key = "stats"
            rest = line.split(":", 1)[1]
            if not is_empty_value(rest):
                stats_lines.append(rest.strip())
            continue

        if line.startswith("General_Revision_Request:"):
            current_key = "general"
            rest = line.split(":", 1)[1]
            if not is_empty_value(rest):
                general_lines.append(rest.strip())
            continue

        if current_key is None:
            continue

        if not line.strip():
            continue
        if is_placeholder(line.strip()):
            continue

        if current_key == "rarity":
            rarity_lines.append(line.rstrip())
        elif current_key == "ability":
            ability_lines.append(line.rstrip())
        elif current_key == "stats":
            stats_lines.append(line.rstrip())
        elif current_key == "general":
            general_lines.append(line.rstrip())

    rarity_req = "\n".join([x for x in rarity_lines if not is_empty_value(x)]).strip()
    ability_req = "\n".join([x for x in ability_lines if not is_empty_value(x)]).strip()
    stats_req = "\n".join([x for x in stats_lines if not is_empty_value(x)]).strip()
    general_req = "\n".join([x for x in general_lines if not is_empty_value(x)]).strip()

    allowed_paths: set[str] = set()
    if rarity_req:
        allowed_paths.update({"/content/RARITY_TEXT", "/content/RARITY_ICON"})
    if ability_req:
        allowed_paths.add("/content/ABILITY_TEXT")
    if stats_req:
        allowed_paths.update({"/content/STAT_LORE", "/content/STAT_CONTEXT", "/content/STAT_COMPLEXITY"})
    if general_req:
        # General revision unlocks ALL content fields plus model_prompt
        allowed_paths.update({
            "/content/NUMBER", "/content/SERIES",
            "/content/WORD", "/content/GLOSS", "/content/CARD_TYPE",
            "/content/RARITY_TEXT", "/content/RARITY_ICON",
            "/content/ART_PROMPT", "/content/ABILITY_TEXT",
            "/content/STAT_LORE", "/content/STAT_CONTEXT", "/content/STAT_COMPLEXITY",
            "/content/OT_VERSE_LINE", "/content/NT_VERSE_LINE",
            "/content/OT_VERSE_REF", "/content/OT_VERSE_SNIPPET",
            "/content/NT_VERSE_REF", "/content/NT_VERSE_SNIPPET",
            "/content/GREEK", "/content/GREEK_TRANSLIT",
            "/content/HEBREW", "/content/HEBREW_TRANSLIT",
            "/content/OT_REFS", "/content/NT_REFS",
            "/content/TRIVIA_BULLETS",
            "/content/WILD_ID", "/content/WILD_COUNTS_AS",
            "/content/QUARTET_ID", "/content/LETTER", "/content/NOTES_INTERNAL",
            "/model_prompt",  # Allow updating the generation prompt
        })

    if not allowed_paths:
        return "", set()

    out_lines: list[str] = []
    if rarity_req:
        out_lines.append("Rarity change request:")
        out_lines.append(rarity_req)
    if ability_req:
        if out_lines:
            out_lines.append("")
        out_lines.append("Ability change request:")
        out_lines.append(ability_req)

    if stats_req:
        if out_lines:
            out_lines.append("")
        out_lines.append("Stats change request:")
        out_lines.append(stats_req)

    if general_req:
        if out_lines:
            out_lines.append("")
        out_lines.append("General revision request (you may modify any content field as needed):")
        out_lines.append(general_req)

    return "\n".join(out_lines).strip(), allowed_paths


def _seed_revise_file(card_dir: Path) -> None:
    target = card_dir / "revise.txt"
    if target.exists():
        return
    template_path = Path("templates") / "revise_template.txt"
    if not template_path.exists():
        return
    target.write_text(_read_text(template_path), encoding="utf-8")


def _json_pointer_tokens(ptr: str) -> list[str]:
    if ptr == "":
        return []
    if not ptr.startswith("/"):
        raise RuntimeError(f"Invalid JSON pointer: {ptr}")
    parts = ptr.split("/")[1:]
    return [p.replace("~1", "/").replace("~0", "~") for p in parts]


def _get_parent_and_key(doc, tokens: list[str]):
    if not tokens:
        raise RuntimeError("Cannot operate on document root")

    cur = doc
    for t in tokens[:-1]:
        if isinstance(cur, list):
            idx = int(t)
            cur = cur[idx]
        else:
            cur = cur[t]
    return cur, tokens[-1]


def _apply_json_patch(doc: dict, patch_ops: list[dict]) -> dict:
    if not isinstance(patch_ops, list):
        raise RuntimeError("Patch must be a JSON array")

    for op in patch_ops:
        if not isinstance(op, dict):
            raise RuntimeError("Patch operations must be objects")

        kind = op.get("op")
        path = op.get("path")
        if not isinstance(kind, str) or not isinstance(path, str):
            raise RuntimeError("Patch operation must include string 'op' and 'path'")

        tokens = _json_pointer_tokens(path)
        parent, key = _get_parent_and_key(doc, tokens)

        if kind in ("add", "replace"):
            if "value" not in op:
                raise RuntimeError(f"Patch op {kind} missing 'value'")
            value = op["value"]

            if isinstance(parent, list):
                if key == "-":
                    parent.append(value)
                else:
                    idx = int(key)
                    if kind == "add":
                        parent.insert(idx, value)
                    else:
                        parent[idx] = value
            else:
                parent[key] = value
            continue

        if kind == "remove":
            if isinstance(parent, list):
                idx = int(key)
                del parent[idx]
            else:
                del parent[key]
            continue

        raise RuntimeError(f"Unsupported patch op: {kind}")

    return doc


def build_prompt_text(card: dict) -> str:
    content = card.get("content", {})
    if not content:
        # Fallback to old behavior if no content dict
        recipe = card.get("model_prompt", "").strip()
        payload = json.dumps(card, ensure_ascii=False, indent=2)
        return f"{recipe}\n\nCARD_JSON:\n{payload}\n"

    # Load the text template
    template_path = Path(__file__).parent.parent / "templates" / "card_style_prompt_template.txt"
    if not template_path.exists():
        # Fallback if template missing
        print(f"Warning: Template {template_path} not found. Using legacy JSON prompt.")
        recipe = card.get("model_prompt", "").strip()
        payload = json.dumps(card, ensure_ascii=False, indent=2)
        return f"{recipe}\n\nCARD_JSON:\n{payload}\n"
        
    with open(template_path, "r", encoding="utf-8") as f:
        template_str = f.read()
    
    # Prepare data for formatting
    data = dict(content)
    
    # Format trivia bullets
    trivia = data.get("TRIVIA_BULLETS", [])
    if isinstance(trivia, list):
        formatted_trivia = "\n".join([f"• {item}" for item in trivia])
        data["TRIVIA_BULLETS_FORMATTED"] = formatted_trivia
    else:
        data["TRIVIA_BULLETS_FORMATTED"] = ""

    # Add rarity visual description
    rarity = str(data.get("RARITY_TEXT", "COMMON")).upper()
    rarity_desc_map = {
        "COMMON": "COMMON with white diamond icon",
        "UNCOMMON": "UNCOMMON with green diamond icon",
        "RARE": "RARE with gold diamond icon",
        "GLORIOUS": "GLORIOUS with orange diamond icon"
    }
    # We update the value passed to the template, but not the underlying card dict
    data["RARITY_TEXT"] = rarity_desc_map.get(rarity, f"{rarity} with white diamond icon")
        
    # Fill template
    try:
        return template_str.format(**data)
    except KeyError as e:
        print(f"Warning: Missing key {e} for prompt template. Falling back to legacy.")
        recipe = card.get("model_prompt", "").strip()
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
            
            # Calculate needed rarities from stats
            stats = _load_series_stats(series_dir)
            needed_rarities = []
            for _ in range(needed):
                nr = _get_needed_rarity(stats)
                needed_rarities.append(nr)
                stats["counts"][nr] = stats["counts"].get(nr, 0) + 1
                stats["total"] += 1
            
            _log(f"[plan] needed rarities based on stats: {needed_rarities}")
            queue.extend(_generate_queue_entries(count=needed, existing_words=existing_words, needed_rarities=needed_rarities))
            save_queue(queue_path, queue)

    if not queue:
        print("Queue empty.")
        return 0

    print(f"Queue entries: {len(queue)}")

    while queue:
        entry = queue[0]
        word = str(entry["word"]).upper()
        slug = slugify(str(entry["word"]))

        existing_for_slug = glob.glob(str(cards_dir / f"[0-9][0-9][0-9]-{slug}"))
        if existing_for_slug:
            print(f"Word already exists as card folder: {existing_for_slug[0]}. Dropping queue entry {word}.")
            queue = queue[1:]
            save_queue(queue_path, queue)
            continue

        number = next_number(cards_dir)
        card_dir = cards_dir / f"{number:03d}-{slug}"
        break

    if not queue:
        print("Queue empty.")
        return 0

    if not template_path.exists():
        print(f"Missing {template_path}")
        return 1

    _log(f"[phase plan] template exists: {template_path}")

    card = read_json(template_path)
    card.setdefault("content", {})

    card_type = str(entry.get("card_type", "NOUN")).upper()
    rarity = str(entry.get("rarity", "COMMON")).upper()
    
    # Optional queue overrides
    q_ability = entry.get("ability")
    q_gloss = entry.get("gloss")
    q_art_prompt = entry.get("art_prompt")
    q_stats = entry.get("stats") if isinstance(entry.get("stats"), dict) else None
    q_ot_verse = entry.get("ot_verse") if isinstance(entry.get("ot_verse"), dict) else None
    q_nt_verse = entry.get("nt_verse") if isinstance(entry.get("nt_verse"), dict) else None
    q_greek = entry.get("greek") if isinstance(entry.get("greek"), dict) else None
    q_hebrew = entry.get("hebrew") if isinstance(entry.get("hebrew"), dict) else None
    q_ot_refs = entry.get("ot_refs")
    q_nt_refs = entry.get("nt_refs")
    q_trivia = entry.get("trivia") if isinstance(entry.get("trivia"), list) else None

    _log(f"[phase plan] selected entry: #{number:03d} word={word} type={card_type} rarity={rarity}")
    if q_ability:
        _log(f"[phase plan] using provided ability: {str(q_ability)[:50]}...")

    if auto:
        _log("[phase plan] auto mode: generating recipe")
        recipe = _generate_card_recipe(number=number, word=word, card_type=card_type, rarity=rarity, ability=q_ability)
        grounding = recipe.get("grounding", {}) if isinstance(recipe.get("grounding"), dict) else {}
        stats = q_stats if q_stats else (recipe.get("stats", {}) if isinstance(recipe.get("stats"), dict) else {})
        ot_verse = q_ot_verse if q_ot_verse else (recipe.get("ot_verse", {}) if isinstance(recipe.get("ot_verse"), dict) else {})
        nt_verse = q_nt_verse if q_nt_verse else (recipe.get("nt_verse", {}) if isinstance(recipe.get("nt_verse"), dict) else {})
        greek = q_greek if q_greek else (recipe.get("greek", {}) if isinstance(recipe.get("greek"), dict) else {})
        hebrew = q_hebrew if q_hebrew else (recipe.get("hebrew", {}) if isinstance(recipe.get("hebrew"), dict) else {})
        trivia = q_trivia if q_trivia else recipe.get("trivia", [])
        if not isinstance(trivia, list):
            trivia = []

        gloss = str(q_gloss).strip() if q_gloss else str(recipe.get("gloss", "")).strip()
        art_prompt = str(q_art_prompt).strip() if q_art_prompt else str(recipe.get("art_prompt", "")).strip()
        ability_text = str(q_ability).strip() if q_ability else str(recipe.get("ability_text", "")).strip()

        ot_ref = str(ot_verse.get("ref", "")).strip()
        ot_snip = str(ot_verse.get("snippet", "")).strip()
        nt_ref = str(nt_verse.get("ref", "")).strip()
        nt_snip = str(nt_verse.get("snippet", "")).strip()

        card["content"]["NUMBER"] = f"{number:03d}"
        card["content"]["SERIES"] = series_dir.name
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

        card["content"]["OT_REFS"] = str(q_ot_refs).strip() if q_ot_refs else str(recipe.get("ot_refs", "")).strip()
        card["content"]["NT_REFS"] = str(q_nt_refs).strip() if q_nt_refs else str(recipe.get("nt_refs", "")).strip()
        card["content"]["TRIVIA_BULLETS"] = [str(x).strip() for x in trivia if str(x).strip()]

        card["grounding"] = grounding

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
            "sources": grounding.get("sources", []) if isinstance(grounding.get("sources"), list) else [],
            "search_queries": grounding.get("queries", []) if isinstance(grounding.get("queries"), list) else [],
        }

        card_dir.mkdir(parents=True, exist_ok=True)
        with open(card_dir / "meta.yml", "w", encoding="utf-8") as f:
            yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True)
        _log(f"[phase plan] wrote meta.yml")
    else:
        _log("[phase plan] manual mode: using canned demo content")
        card["content"]["NUMBER"] = f"{number:03d}"
        card["content"]["SERIES"] = series_dir.name
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
    _log(f"[phase plan] wrote card.json")

    prompt_text = build_prompt_text(card)
    with open(card_dir / "prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt_text)
    _log(f"[phase plan] wrote prompt.txt")

    _seed_revise_file(card_dir)
    _log(f"[phase plan] wrote revise.txt")

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

    # Write to GITHUB_OUTPUT if running in GitHub Actions
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"card_dir={card_dir}\n")
            f.write(f"card_slug={card_dir.name}\n")
        _log(f"[phase plan] wrote card_dir={card_dir} to GITHUB_OUTPUT")

    # Update series stats
    stats = _load_series_stats(series_dir)
    stats["counts"][rarity] = stats["counts"].get(rarity, 0) + 1
    stats["total"] = sum(stats["counts"].values())
    _save_series_stats(series_dir, stats)
    _log(f"[phase plan] updated stats.yml: {rarity} count now {stats['counts'][rarity]}, total {stats['total']}")

    return 0


def phase_demo(*, series_dir: Path, template_path: Path, demo_dir: Path) -> int:
    if yaml is None:
        raise RuntimeError("pyyaml is required. Install with: pip install pyyaml")

    _log(f"[phase demo] demo_dir={demo_dir}")
    _log(f"[phase demo] template_path={template_path}")

    cards_dir = demo_dir
    number = next_number(cards_dir)

    entry = _pick_demo_entry()
    word = str(entry["word"]).upper()
    slug = slugify(word)
    card_type = str(entry.get("card_type", "NOUN")).upper()
    rarity = str(entry.get("rarity", "COMMON")).upper()

    _log(f"[phase demo] selected: #{number:03d} word={word} type={card_type} rarity={rarity}")

    card_dir = cards_dir / f"{number:03d}-{slug}"
    os.makedirs(card_dir, exist_ok=True)

    if not template_path.exists():
        print(f"Missing {template_path}")
        return 1

    _log("[phase demo] generating recipe")
    recipe = _generate_card_recipe(number=number, word=word, card_type=card_type, rarity=rarity)
    grounding = recipe.get("grounding", {}) if isinstance(recipe.get("grounding"), dict) else {}
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
    card["content"]["SERIES"] = series_dir.name
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

    card["grounding"] = grounding

    write_json(card_dir / "card.json", card)
    _log(f"[phase demo] wrote card.json")

    prompt_text = build_prompt_text(card)
    with open(card_dir / "prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt_text)
    _log(f"[phase demo] wrote prompt.txt")

    _seed_revise_file(card_dir)
    _log(f"[phase demo] wrote revise.txt")

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
        "sources": grounding.get("sources", []) if isinstance(grounding.get("sources"), list) else [],
        "search_queries": grounding.get("queries", []) if isinstance(grounding.get("queries"), list) else [],
    }
    with open(card_dir / "meta.yml", "w", encoding="utf-8") as f:
        yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True)
    _log(f"[phase demo] wrote meta.yml")

    out_png = card_dir / "outputs" / "card_1024x1536.png"
    _log(f"[phase demo] generating image -> {out_png}")
    
    style_refs, rarity_labels = _build_style_refs(DEFAULT_DEMO_DIR.parent)
    if style_refs:
        cmd = [
            sys.executable,
            str(Path("tools") / "gemini_style.py"),
            "--prompt-file", str(card_dir / "prompt.txt"),
            *_build_style_cmd_args(style_refs, rarity_labels, rarity),
            "--out", str(out_png)
        ]
    else:
        cmd = [
            sys.executable,
            str(Path("tools") / "gemini_image.py"),
            str(card_dir / "prompt.txt"),
            str(out_png)
        ]
        
    subprocess.check_call(cmd)
    
    # Run polish step
    polish_cmd = [
        sys.executable,
        str(Path("tools") / "polish_card.py"),
        str(out_png)
    ]
    try:
        subprocess.check_call(polish_cmd)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Polish step failed: {e}")

    _run_watermark(card_dir=card_dir, image_path=out_png)
        
    _log("[phase demo] image generation complete")

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


def phase_imagegen(*, series_dir: Path) -> int:
    cards_dir = series_dir / "cards"
    out_name = "card_1024x1536.png"

    _log(f"[phase imagegen] cards_dir={cards_dir}")
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

    # Get target rarity from meta.yml
    target_rarity = None
    meta_file = target_dir / "meta.yml"
    if meta_file.exists() and yaml:
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}
        target_rarity = meta.get("rarity", "").upper() or None

    _log(f"[phase imagegen] generating image for {target_dir.name} -> {out_png} (rarity={target_rarity})")
    
    style_refs, rarity_labels = _build_style_refs(series_dir)
    if style_refs:
        cmd = [
            sys.executable,
            str(Path("tools") / "gemini_style.py"),
            "--prompt-file", str(prompt_file),
            *_build_style_cmd_args(style_refs, rarity_labels, target_rarity),
            "--out", str(out_png)
        ]
    else:
        cmd = [
            sys.executable,
            str(Path("tools") / "gemini_image.py"),
            str(prompt_file),
            str(out_png)
        ]
        
    subprocess.check_call(cmd)

    # Run polish step to remove lingering brackets
    polish_cmd = [
        sys.executable,
        str(Path("tools") / "polish_card.py"),
        str(out_png)
    ]
    try:
        subprocess.check_call(polish_cmd)
        _log("[phase imagegen] polish complete")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Polish step failed: {e}")

    _run_watermark(card_dir=target_dir, image_path=out_png)

    print(f"Rendered image at {out_png}")
    return 0


def _generate_image_for_card_dir(*, card_dir: Path) -> int:
    out_name = "card_1024x1536.png"
    prompt_file = card_dir / "prompt.txt"
    if not prompt_file.exists():
        print(f"Missing {prompt_file}")
        return 1

    out_png = card_dir / "outputs" / out_name
    out_png.parent.mkdir(parents=True, exist_ok=True)

    # Get target rarity from meta.yml
    target_rarity = None
    meta_file = card_dir / "meta.yml"
    if meta_file.exists() and yaml:
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}
        target_rarity = meta.get("rarity", "").upper() or None

    _log(f"[batch] generating image for {card_dir.name} -> {out_png} (rarity={target_rarity})")
    
    # Infer series_dir from card_dir (card_dir is series/XXXX/cards/NNN-word)
    series_dir = card_dir.parent.parent
    style_refs, rarity_labels = _build_style_refs(series_dir)
    if style_refs:
        cmd = [
            sys.executable,
            str(Path("tools") / "gemini_style.py"),
            "--prompt-file", str(prompt_file),
            *_build_style_cmd_args(style_refs, rarity_labels, target_rarity),
            "--out", str(out_png)
        ]
    else:
        cmd = [
            sys.executable,
            str(Path("tools") / "gemini_image.py"),
            str(prompt_file),
            str(out_png)
        ]
        
    subprocess.check_call(cmd)
    
    # Run polish step
    polish_cmd = [
        sys.executable,
        str(Path("tools") / "polish_card.py"),
        str(out_png)
    ]
    try:
        subprocess.check_call(polish_cmd)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Polish step failed: {e}")

    _run_watermark(card_dir=card_dir, image_path=out_png)
        
    print(f"Rendered image at {out_png}")
    return 0


def phase_batch(*, series_dir: Path, template_path: Path, auto: bool, batch: int) -> int:
    cards_dir = series_dir / "cards"
    for i in range(batch):
        _log(f"[batch] run {i + 1}/{batch} starting")
        before = find_latest_card_dir(cards_dir)
        rc = phase_plan(series_dir=series_dir, template_path=template_path, auto=auto)
        if rc != 0:
            return rc
        after = find_latest_card_dir(cards_dir)
        if after is None or after == before:
            _log("[batch] no new card planned; stopping")
            return 0
        rc = _generate_image_for_card_dir(card_dir=after)
        if rc != 0:
            return rc
        _log(f"[batch] run {i + 1}/{batch} complete")
    return 0


def phase_revise(*, card_dir: Path, revise_file: Path | None) -> int:
    if yaml is None:
        raise RuntimeError("pyyaml is required. Install with: pip install pyyaml")

    _log(f"[phase revise] card_dir={card_dir}")

    card_path = card_dir / "card.json"
    if not card_path.exists():
        print(f"Missing {card_path}")
        return 1

    revise_path = revise_file if revise_file is not None else (card_dir / "revise.txt")
    if not revise_path.exists():
        print(f"Missing {revise_path}. Add your edit instructions there and rerun revise.")
        return 1

    raw_instructions = _read_text(revise_path)
    instructions, allowed_paths = _parse_revise_form(raw_instructions)
    if not instructions:
        print(
            f"No revision instructions found in {revise_path}. "
            "Edit revise.txt (add non-comment text) and rerun revise."
        )
        return 1

    card = read_json(card_path)

    allowed_paths_str = ", ".join(sorted(allowed_paths))
    rules_appendix = _load_rules_appendix()
    prompt = (
        "You are revising a Bible word-study trading card JSON. "
        "Return ONLY a JSON Patch array (RFC 6902) to apply to the provided CARD_JSON.\n"
        "The patch must only modify keys under: /content or /model_prompt. "
        "Do NOT modify /render_instructions, /style_guide, or /layout.\n"
        "Follow game rules: there is ONE shared deck; do not say 'your deck'. "
        "Allowed ops: add, replace. Do not use remove/move/copy/test.\n\n"
        "IMPORTANT: Only make changes that are EXPLICITLY requested in the HUMAN_EDIT_INSTRUCTIONS below. "
        "Do NOT make any other changes, improvements, or reformatting beyond what was asked.\n\n"
        "GAME RULES (must follow):\n"
        + GAME_RULES_SNIPPET
        + rules_appendix
        + "\n\n"
        + FORMATTING_RUBRIC
        + "\n\n"
        "HUMAN_EDIT_INSTRUCTIONS (ONLY make these specific changes):\n"
        + instructions
        + "\n\n"
        "CARD_JSON:\n"
        + json.dumps(card, ensure_ascii=False, indent=2)
    )

    _log("[phase revise] requesting JSON Patch from Gemini")
    text = generate_text(prompt, model="gemini-3-pro-preview", temperature=0.2, use_google_search=False)
    patch_ops = _parse_json_from_model(text)
    if not isinstance(patch_ops, list):
        raise RuntimeError("Revise step did not return a JSON Patch array.")

    for op in patch_ops:
        if not isinstance(op, dict):
            raise RuntimeError("Patch operations must be objects")
        if op.get("op") not in ("replace", "add"):
            raise RuntimeError(f"Unsupported patch op for revise: {op.get('op')}")
        if op.get("path") not in allowed_paths:
            raise RuntimeError(f"Patch attempted to modify unsupported path: {op.get('path')}")

    updated = _apply_json_patch(card, patch_ops)

    write_json(card_path, updated)
    _log(f"[phase revise] wrote card.json")

    prompt_text = build_prompt_text(updated)
    with open(card_dir / "prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt_text)
    _log(f"[phase revise] wrote prompt.txt")

    out_png = card_dir / "outputs" / "card_1024x1536.png"
    
    # Get target rarity from updated card
    target_rarity = updated.get("content", {}).get("RARITY_TEXT", "").upper() or None
    
    _log(f"[phase revise] generating image -> {out_png} (rarity={target_rarity})")
    
    series_dir = card_dir.parent.parent
    style_refs, rarity_labels = _build_style_refs(series_dir)
    if style_refs:
        cmd = [
            sys.executable,
            str(Path("tools") / "gemini_style.py"),
            "--prompt-file", str(card_dir / "prompt.txt"),
            *_build_style_cmd_args(style_refs, rarity_labels, target_rarity),
            "--out", str(out_png)
        ]
    else:
        cmd = [
            sys.executable,
            str(Path("tools") / "gemini_image.py"),
            str(card_dir / "prompt.txt"),
            str(out_png)
        ]
        
    subprocess.check_call(cmd)
    _log("[phase revise] image generation complete")

    _run_watermark(card_dir=card_dir, image_path=out_png)

    content = updated.get("content", {}) if isinstance(updated.get("content"), dict) else {}
    render_post(
        str(card_dir / "post.md"),
        word=str(content.get("WORD", "")),
        gloss=str(content.get("GLOSS", "")),
        ot_ref=str(content.get("OT_VERSE_REF", "")),
        ot_snip=str(content.get("OT_VERSE_SNIPPET", "")),
        nt_ref=str(content.get("NT_VERSE_REF", "")),
        nt_snip=str(content.get("NT_VERSE_SNIPPET", "")),
        trivia_items=content.get("TRIVIA_BULLETS", []) if isinstance(content.get("TRIVIA_BULLETS"), list) else [],
        image_rel_path=f"./outputs/{out_png.name}",
    )

    meta_path = card_dir / "meta.yml"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}
        if not isinstance(meta, dict):
            meta = {}
        prev = meta.get("revision")
        try:
            prev_i = int(prev) if prev is not None else 0
        except Exception:
            prev_i = 0
        meta["revision"] = prev_i + 1
        meta["revision_notes"] = instructions
        with open(meta_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True)

    print(f"Revised card at {card_dir}")
    return 0


def phase_rebuild(*, card_dir: Path, regen_prompt: bool) -> int:
    card_path = card_dir / "card.json"
    if not card_path.exists():
        print(f"Missing {card_path}")
        return 1

    _log(f"[phase rebuild] card_dir={card_dir} regen_prompt={bool(regen_prompt)}")

    card = read_json(card_path)

    prompt_txt = card_dir / "prompt.txt"
    prompt_json = card_dir / "prompt.json"
    prompt_path = prompt_txt if prompt_txt.exists() else prompt_json

    if regen_prompt or not prompt_txt.exists():
        prompt_text = build_prompt_text(card)
        with open(prompt_txt, "w", encoding="utf-8") as f:
            f.write(prompt_text)
        prompt_path = prompt_txt
        _log(f"[phase rebuild] wrote prompt.txt")

    out_png = card_dir / "outputs" / "card_1024x1536.png"
    
    # Get target rarity from card
    target_rarity = card.get("content", {}).get("RARITY_TEXT", "").upper() or None
    
    _log(f"[phase rebuild] generating image -> {out_png} (rarity={target_rarity})")
    
    series_dir = card_dir.parent.parent
    style_refs, rarity_labels = _build_style_refs(series_dir)
    if style_refs:
        cmd = [
            sys.executable,
            str(Path("tools") / "gemini_style.py"),
            "--prompt-file", str(prompt_path),
            *_build_style_cmd_args(style_refs, rarity_labels, target_rarity),
            "--out", str(out_png)
        ]
    else:
        cmd = [
            sys.executable,
            str(Path("tools") / "gemini_image.py"),
            str(prompt_path),
            str(out_png)
        ]
        
    subprocess.check_call(cmd)
    _log("[phase rebuild] image generation complete")

    _run_watermark(card_dir=card_dir, image_path=out_png)

    content = card.get("content", {}) if isinstance(card.get("content"), dict) else {}
    render_post(
        str(card_dir / "post.md"),
        word=str(content.get("WORD", "")),
        gloss=str(content.get("GLOSS", "")),
        ot_ref=str(content.get("OT_VERSE_REF", "")),
        ot_snip=str(content.get("OT_VERSE_SNIPPET", "")),
        nt_ref=str(content.get("NT_VERSE_REF", "")),
        nt_snip=str(content.get("NT_VERSE_SNIPPET", "")),
        trivia_items=content.get("TRIVIA_BULLETS", []) if isinstance(content.get("TRIVIA_BULLETS"), list) else [],
        image_rel_path=f"./outputs/{out_png.name}",
    )
    print(f"Rebuilt card assets at {card_dir}")
    return 0


def _generate_image_only(*, card_dir: Path) -> Path:
    """Generate image without polish. Returns path to generated image."""
    out_name = "card_1024x1536.png"
    prompt_file = card_dir / "prompt.txt"
    if not prompt_file.exists():
        raise RuntimeError(f"Missing {prompt_file}")

    out_png = card_dir / "outputs" / out_name
    out_png.parent.mkdir(parents=True, exist_ok=True)

    # Get target rarity from meta.yml
    target_rarity = None
    meta_file = card_dir / "meta.yml"
    if meta_file.exists() and yaml:
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}
        target_rarity = meta.get("rarity", "").upper() or None

    _log(f"[imagegen] generating image for {card_dir.name} -> {out_png} (rarity={target_rarity})")

    series_dir = card_dir.parent.parent
    style_refs, rarity_labels = _build_style_refs(series_dir)
    if style_refs:
        cmd = [
            sys.executable,
            str(Path("tools") / "gemini_style.py"),
            "--prompt-file", str(prompt_file),
            *_build_style_cmd_args(style_refs, rarity_labels, target_rarity),
            "--out", str(out_png)
        ]
    else:
        cmd = [
            sys.executable,
            str(Path("tools") / "gemini_image.py"),
            str(prompt_file),
            str(out_png)
        ]

    subprocess.check_call(cmd)
    return out_png


def _run_polish(image_path: Path) -> None:
    """Run polish step to remove brackets."""
    polish_cmd = [
        sys.executable,
        str(Path("tools") / "polish_card.py"),
        str(image_path)
    ]
    try:
        subprocess.check_call(polish_cmd)
        _log("[polish] bracket removal complete")
    except subprocess.CalledProcessError as e:
        _log(f"[polish] Warning: Polish step failed: {e}")


def _run_watermark(*, card_dir: Path, image_path: Path) -> None:
    """Generate watermark.svg and burn it into the PNG (bottom-right)."""
    watermark_svg = card_dir / "watermark.svg"
    cmd_svg = [
        sys.executable,
        str(Path("tools") / "watermark.py"),
        "--card-dir",
        str(card_dir),
        "--out",
        str(watermark_svg),
    ]
    cmd_apply = [
        sys.executable,
        str(Path("tools") / "apply_watermark.py"),
        "--card-dir",
        str(card_dir),
        "--in",
        str(image_path),
    ]

    try:
        r1 = subprocess.run(cmd_svg, capture_output=True, text=True, check=True)
        r2 = subprocess.run(cmd_apply, capture_output=True, text=True, check=True)
        _log("[watermark] applied watermark")
    except subprocess.CalledProcessError as e:
        stdout = (e.stdout or "").strip()
        stderr = (e.stderr or "").strip()
        _log(f"[watermark] Warning: watermark step failed: {e}")
        if stdout:
            _log(f"[watermark] stdout: {stdout}")
        if stderr:
            _log(f"[watermark] stderr: {stderr}")


def phase_review(*, card_dir: Path, max_attempts: int = 2) -> int:
    """
    Multi-stage review of a generated card image with iterative improvement.

    New Flow:
    1. DESCRIBE: Have LLM describe what it sees on the card (observation only)
    2. SCORE: Compare description against rubric in separate call (judgment)
    3. DECIDE: If score < 90, rebuild. If score >= 90 but < 100, revise.
    4. ITERATE: Try up to max_attempts times to reach 100/100
    5. FLAG: If not 100 after max_attempts, flag warning for user to revise

    Returns 0 on success (score >= 90), 1 on failure.
    """
    if yaml is None:
        raise RuntimeError("pyyaml is required. Install with: pip install pyyaml")

    _log(f"[phase review] card_dir={card_dir}")

    card_path = card_dir / "card.json"
    if not card_path.exists():
        print(f"Missing {card_path}")
        return 1

    out_png = card_dir / "outputs" / "card_1024x1536.png"
    if not out_png.exists():
        print(f"Missing {out_png}. Run imagegen first.")
        return 1

    card_json = read_json(card_path)
    word = card_json.get("content", {}).get("WORD", "UNKNOWN")

    best_score = 0
    best_result: ReviewResult | None = None
    all_descriptions: list[CardDescription] = []

    for attempt in range(1, max_attempts + 1):
        _log(f"[phase review] === ATTEMPT {attempt}/{max_attempts} for {word} ===")

        # Stage 1: DESCRIBE - Have LLM observe the card
        _log(f"[phase review] Stage 1: Describing card...")
        try:
            description = describe_card(out_png)
            all_descriptions.append(description)
        except Exception as e:
            _log(f"[phase review] Description failed: {e}")
            return 1

        # Print what the LLM sees
        print("\n" + "=" * 60)
        print(format_description_report(description))
        print("=" * 60 + "\n")

        # Stage 2: SCORE - Compare description against rubric
        _log(f"[phase review] Stage 2: Scoring against rubric...")
        try:
            result = score_against_rubric(description, card_json)
            result.passed = result.score >= 90
        except Exception as e:
            _log(f"[phase review] Scoring failed: {e}")
            return 1

        _log(f"[phase review] Score: {result.score}/100")

        # Print score breakdown
        print("\n" + "-" * 40)
        for name, data in result.categories.items():
            score = data.get("score", 0)
            max_score = data.get("max", 0)
            issues = data.get("issues", [])
            status = "✓" if score == max_score else "⚠" if score >= max_score * 0.7 else "✗"
            print(f"{status} {name.replace('_', ' ').title()}: {score}/{max_score}")
            for issue in issues:
                print(f"    - {issue}")
        print("-" * 40 + "\n")

        if result.corrections:
            print("Corrections needed:")
            for i, correction in enumerate(result.corrections, 1):
                print(f"  {i}. {correction}")
            print()

        if result.score > best_score:
            best_score = result.score
            best_result = result

        # Stage 3: DECIDE - Perfect score means we're done
        if result.score >= 100:
            _log(f"[phase review] Perfect score achieved!")
            break

        # If this is the last attempt, don't regenerate
        if attempt >= max_attempts:
            _log(f"[phase review] Max attempts reached. Final score: {result.score}/100")
            break

        # Stage 4: ITERATE based on score
        if result.score < 90:
            # Score < 90: full rebuild needed
            _log(f"[phase review] Score {result.score} < 90, REBUILDING image...")
            try:
                _generate_image_only(card_dir=card_dir)
            except Exception as e:
                _log(f"[phase review] Image regeneration failed: {e}")
                return 1
        else:
            # Score >= 90 but < 100: targeted revision based on corrections
            _log(f"[phase review] Score {result.score} >= 90, attempting targeted REVISION...")

            # Build revision instructions from corrections
            if result.corrections:
                revision_instructions = _build_revision_from_corrections(description, result.corrections)
                _log(f"[phase review] Auto-revision: {revision_instructions}")

                # Write temporary revise instructions
                revise_path = card_dir / "revise.txt"
                original_revise = None
                if revise_path.exists():
                    with open(revise_path, "r", encoding="utf-8") as f:
                        original_revise = f.read()

                # Write auto-generated revision
                with open(revise_path, "w", encoding="utf-8") as f:
                    f.write(f"# Auto-generated revision from review (attempt {attempt})\n")
                    f.write(f"General_Revision_Request:\n{revision_instructions}\n")

                # Run the image regeneration (not full revise, just image)
                try:
                    _generate_image_only(card_dir=card_dir)
                except Exception as e:
                    _log(f"[phase review] Revision image regeneration failed: {e}")

                # Restore original revise.txt
                if original_revise is not None:
                    with open(revise_path, "w", encoding="utf-8") as f:
                        f.write(original_revise)
            else:
                # No corrections specified, just run polish
                _log(f"[phase review] No specific corrections, running polish...")
                _run_polish(out_png)

    # Update meta.yml with review status
    meta_path = card_dir / "meta.yml"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}
        if not isinstance(meta, dict):
            meta = {}
    else:
        meta = {}

    meta["review_score"] = best_score
    meta["review_attempts"] = max_attempts

    # Store description summary for debugging
    if all_descriptions:
        last_desc = all_descriptions[-1]
        meta["last_description"] = {
            "card_number_format": last_desc.card_number_format,
            "stat_pip_shape": last_desc.stat_pip_shape,
            "stat_pip_fill_color": last_desc.stat_pip_fill_color,
            "has_brackets": last_desc.has_brackets,
            "bracket_locations": last_desc.bracket_locations if last_desc.has_brackets else [],
        }

    if best_score >= 100:
        meta["review_status"] = "green"
        status_msg = "PASS (100%)"
    elif best_score >= 90:
        meta["review_status"] = "yellow"
        status_msg = f"NEEDS MANUAL REVISION ({best_score}%) - review failed to reach 100 after {max_attempts} attempts"
        if best_result and best_result.corrections:
            meta["review_notes"] = "; ".join(best_result.corrections[:3])
        # Add user warning
        meta["user_action_required"] = True
        meta["user_warning"] = f"Card scored {best_score}/100. Please review and revise manually."
    else:
        meta["review_status"] = "red"
        status_msg = f"FAILED ({best_score}%)"
        if best_result and best_result.corrections:
            meta["review_notes"] = "; ".join(best_result.corrections[:3])
        meta["user_action_required"] = True
        meta["user_warning"] = f"Card scored only {best_score}/100. Rebuild required."

    with open(meta_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True)

    _log(f"[phase review] Final status: {status_msg}")
    print(f"\n{'='*60}")
    print(f"Review complete for {word}: {status_msg}")
    if best_score < 100:
        print(f"⚠️  WARNING: Card did not reach 100/100. Manual revision recommended.")
    print(f"{'='*60}\n")

    # Return success if score >= 90 (yellow or green)
    return 0 if best_score >= 90 else 1


def _build_revision_from_corrections(description: CardDescription, corrections: list[str]) -> str:
    """
    Build revision instructions from review corrections and description.

    Focuses on the most common issues: stat pip color, brackets, card number format.
    """
    instructions = []

    # Check for stat pip color issue
    if description.stat_pip_fill_color.lower() not in ("navy", "dark blue", "blue"):
        instructions.append(
            f"CRITICAL: Stat pips are currently {description.stat_pip_fill_color}. "
            "They MUST be NAVY (dark blue) filled circles, not gold or yellow."
        )

    # Check for stat pip shape issue
    if description.stat_pip_shape.lower() != "circle":
        instructions.append(
            f"CRITICAL: Stat pips are {description.stat_pip_shape} shapes. "
            "They MUST be CIRCLES only, never diamonds, squares, or stars."
        )

    # Check for bracket issues
    if description.has_brackets:
        locations = ", ".join(description.bracket_locations) if description.bracket_locations else "various locations"
        instructions.append(
            f"CRITICAL: Remove ALL square brackets [ ]. Found at: {locations}. "
            "Write text directly without any brackets."
        )

    # Check for card number format
    if description.card_number_format and "[" in description.card_number_format:
        instructions.append(
            f"CRITICAL: Card number format is '{description.card_number_format}'. "
            "It MUST be '#XXX' format (e.g., #003), NOT '[#XXX]'."
        )

    # Add any other corrections from the review
    for correction in corrections[:3]:  # Limit to top 3
        if correction not in "\n".join(instructions):
            instructions.append(correction)

    return "\n".join(instructions) if instructions else "Improve image quality and text clarity."


def phase_gallery(*, series_dir: Path, out_dir: Path) -> int:
    """Build the static gallery site."""
    cmd = [
        sys.executable,
        str(Path("tools") / "build_gallery.py"),
        "--series-dir", str(series_dir),
        "--out-dir", str(out_dir)
    ]
    try:
        subprocess.check_call(cmd)
        return 0
    except subprocess.CalledProcessError:
        return 1


def phase_full(*, series_dir: Path, template_path: Path, auto: bool, batch: int) -> int:
    rc = phase_plan(series_dir=series_dir, template_path=template_path, auto=auto)
    if rc != 0:
        return rc
    return phase_imagegen(series_dir=series_dir)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["plan", "imagegen", "demo", "revise", "rebuild", "review", "gallery", "full"], required=True)
    parser.add_argument("--series", default=str(DEFAULT_SERIES_DIR))
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE_PATH))
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--batch", type=int, default=1)
    parser.add_argument("--demo-dir", default=str(DEFAULT_DEMO_DIR))
    parser.add_argument("--card-dir")
    parser.add_argument("--revise-file")
    parser.add_argument("--regen-prompt", action="store_true")
    parser.add_argument("--out-dir", default="_site")
    args = parser.parse_args()

    _log(
        "[cli] "
        + "phase="
        + str(args.phase)
        + " series="
        + str(args.series)
        + " template="
        + str(args.template)
        + (" demo_dir=" + str(args.demo_dir) if hasattr(args, "demo_dir") else "")
        + (" card_dir=" + str(args.card_dir) if getattr(args, "card_dir", None) else "")
        + (" auto=true" if getattr(args, "auto", False) else "")
        + (" regen_prompt=true" if getattr(args, "regen_prompt", False) else "")
    )

    series_dir = Path(args.series)
    template_path = Path(args.template)

    batch = int(getattr(args, "batch", 1) or 1)
    if batch < 1:
        batch = 1
    if batch > 10:
        _log(f"[cli] batch clamped from {batch} to 10")
        batch = 10

    if batch > 1:
        if args.phase == "plan":
            return phase_batch(series_dir=series_dir, template_path=template_path, auto=args.auto, batch=batch)
        if args.phase == "demo":
            for i in range(batch):
                _log(f"[batch demo] run {i + 1}/{batch}")
                rc = phase_demo(series_dir=series_dir, template_path=template_path, demo_dir=Path(args.demo_dir))
                if rc != 0:
                    return rc
            return 0
        if args.phase == "full":
            # For batch full, we just loop phase_full
            for i in range(batch):
                _log(f"[batch full] run {i + 1}/{batch}")
                rc = phase_full(series_dir=series_dir, template_path=template_path, auto=args.auto, batch=1)
                if rc != 0:
                    return rc
            return 0
        print("--batch is only supported with --phase plan, --phase demo, or --phase full")
        return 2

    if args.phase == "full":
        return phase_full(series_dir=series_dir, template_path=template_path, auto=args.auto, batch=1)

    if args.phase == "plan":
        return phase_plan(series_dir=series_dir, template_path=template_path, auto=args.auto)

    if args.phase == "imagegen":
        return phase_imagegen(series_dir=series_dir)

    if args.phase == "demo":
        return phase_demo(series_dir=series_dir, template_path=template_path, demo_dir=Path(args.demo_dir))

    if args.phase == "revise":
        if not args.card_dir:
            print("Missing --card-dir")
            return 2
        revise_file = Path(args.revise_file) if args.revise_file else None
        return phase_revise(card_dir=Path(args.card_dir), revise_file=revise_file)

    if args.phase == "rebuild":
        if not args.card_dir:
            print("Missing --card-dir")
            return 2
        return phase_rebuild(card_dir=Path(args.card_dir), regen_prompt=bool(args.regen_prompt))

    if args.phase == "review":
        if not args.card_dir:
            print("Missing --card-dir")
            return 2
        return phase_review(card_dir=Path(args.card_dir))

    if args.phase == "gallery":
        return phase_gallery(series_dir=series_dir, out_dir=Path(args.out_dir))

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
