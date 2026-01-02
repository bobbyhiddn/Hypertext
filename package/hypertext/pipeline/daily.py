#!/usr/bin/env python3
import argparse
import glob
import json
import os
import random
import signal
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Global shutdown flag for Ctrl+C handling
_shutdown_requested = threading.Event()


def _signal_handler(signum, frame):
    """Handle Ctrl+C by forcing immediate exit."""
    print("\n[CTRL+C] Forcing immediate shutdown...")
    os._exit(1)  # Force exit without cleanup - kills all threads immediately


# Register signal handler for immediate shutdown
signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)

from hypertext.gemini.text import generate_text, generate_text_with_grounding
from hypertext.gemini.review import (
    review_card,
    describe_card,
    describe_card_style_references,
    score_against_rubric,
    format_review_report,
    format_description_report,
    ReviewResult,
    CardDescription,
)
from hypertext.cards.render import render_post

try:
    import yaml
except ImportError:
    yaml = None

DEFAULT_SERIES_DIR = Path("series/2026-Q1")
DEFAULT_TEMPLATE_PATH = Path("templates/card_prompt_template.json")
DEFAULT_DEMO_DIR = Path("demo_cards")
RULES_PATH = Path("docs/rules.md")

# Game rules snippet for ability generation guidance
GAME_RULES_SNIPPET = (
    "GAME MECHANICS:\n"
    "- There is ONE shared 90-card deck (the 'Tower'). Say 'the Tower' or 'the deck', never 'your deck'.\n"
    "- Players have hands, Pages (face-up scored cards), and access to Sheol (shared discard).\n"
    "- Scoring: Complete a phase (5-7 cards matching a type pattern) = score points.\n"
    "- 'Letters' are tokens earned by completing your Lot (personal phase).\n\n"
    "ABILITY DESIGN PRINCIPLES:\n"
    "- THE WORD DEFINES THE ABILITY. Ask: 'What does this word MEAN?' then design an ability that EMBODIES that meaning.\n"
    "- Example: SCATTER = disperse things → 'Each player discards 1, then draws 1'\n"
    "- Example: REFUGE = safety/shelter → 'Your Pages cannot be targeted this turn'\n"
    "- Example: HARVEST = gathering crops → 'Add the top card of Sheol to your hand'\n"
    "- The mechanic MUST make sense for the word. A player should read the ability and think 'yes, that fits!'\n"
    "- Be CREATIVE and UNIQUE. Avoid formulaic patterns.\n"
    "- One short-to-medium sentence. Clear, memorable, flavorful.\n\n"
    "BANNED (never use):\n"
    "- 'Draw a card' as the ENTIRE ability with no flavor (boring, no theme)\n"
    "- 'Search the Tower/deck' effects (too powerful, slows game)\n"
    "- Generic effects with no thematic connection\n"
    "- Abilities that just copy other cards in the set\n\n"
    "DRAWING IS FINE when thematic! Examples:\n"
    "- GOOD: 'Draw 1, then return a card from hand to top of Tower' (thematic to gathering)\n"
    "- GOOD: 'Draw 2, discard 1' (thematic to water/satisfaction)\n"
    "- GOOD: 'Draw 1 for each NAME in your Pages' (thematic to legacy)\n"
    "- BAD: 'Draw 2 cards' (no flavor, no theme, boring)\n\n"
    "ABILITY INSPIRATION BY RARITY:\n"
    "- COMMON: Simple value with flavor (e.g., BREAD: 'Look at top 3 of Tower, add 1 to hand')\n"
    "- UNCOMMON: Type-based or conditional (e.g., SHEPHERD: 'Return a NAME from Sheol to your hand')\n"
    "- RARE: Stat-based, player interaction, or powerful effects "
    "(e.g., PROPHET: 'Name a card type; target player must discard one of that type or reveal their hand')\n"
    "- GLORIOUS: Unique, game-changing, deeply thematic "
    "(e.g., RESURRECTION: 'Return up to 3 cards from Sheol to the Tower, then each player draws 1')\n\n"
    "CREATIVE MECHANICS TO USE:\n"
    "- Player interaction: 'target player' (can target yourself for strategic benefit!) discards, reveals hand, etc.\n"
    "- Sheol manipulation: return cards, exile cards, peek, shuffle into Tower, 'bury' cards face-down\n"
    "- Tower manipulation: look at top X, rearrange top cards, put cards on bottom, mill cards to Sheol\n"
    "- Letter economy: gain Letters, steal Letters, convert Letters to cards\n"
    "- Phase/Lot manipulation: swap Lots with target player, peek at Lots, record to target player's Lot\n"
    "- Stat comparisons: if LORE > target's LORE, then... (compare any stat between cards)\n"
    "- Pages-based effects: for each NOUN in your Pages, do X; bonus if you control all 5 types\n"
    "- Conditional triggers: if you have no NAMEs in hand; if Sheol has 10+ cards; if you're behind in points\n"
    "- Turn order effects: reverse turn order, skip next player, take extra turn\n"
    "- Protection effects: prevent target player from targeting your Pages/hand this round\n"
    "- Copying effects: use another card's ability from Sheol, repeat your last ability\n"
    "- Trade effects: swap a card with target player, exchange top card of Tower with Sheol\n"
    "- Reveal effects: reveal top X of Tower, target player chooses one for you (or vice versa)\n"
    "- Threshold effects: if your Pages have 3+ ADJECTIVEs, this ability is upgraded\n"
    "- Type matching: discard 2-4 cards of the same type for scaling effects (e.g., 'Discard 2 NOUNs: draw 3')\n"
    "- Redeem interaction: prevent opponents from redeeming this turn, or force a redeem\n"
    "- Hand size matters: bonus if you have 7+ cards, or if fewer cards than opponent\n"
    "- TITLE/wild synergy: TITLEs count as NOUN or NAME—effects that reward or punish wilds\n"
    "- Stat totals: add LORE across your Pages, if total > 10 then gain bonus\n"
    "- Rarity matters: if you control a GLORIOUS in Pages, this ability is stronger\n"
    "- Racing effects: bonus if you have fewer cards in hand than opponents (racing to empty)\n"
    "- Silence: target player cannot activate abilities this turn\n"
    "- All-players effects: each player draws 1, each player discards a NOUN, etc.\n"
    "- Letter-paid bonus (RARE): if a Letter was spent to activate this, gain a bonus effect\n"
    "- Sacrifice Pages (GLORIOUS only, very rare): discard from your PAGES for devastating effects\n"
    "- Sacrifice Letters (GLORIOUS only, very rare): spend Letters for game-changing power"
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


# Use absolute path so it works in parallel workers regardless of cwd
_THIS_DIR = Path(__file__).resolve().parent
DEFAULT_STYLE_TEMPLATE = _THIS_DIR.parent / "templates" / "card_template.png"
DEFAULT_STYLE_RUBRIC = _THIS_DIR.parent / "templates" / "card_style_rubric.txt"

# Versioned template directory (repo-level, not package)
_REPO_ROOT = _THIS_DIR.parent.parent.parent
_CARD_TEMPLATE_DIR = _REPO_ROOT / "templates" / "card"

RARITY_ORDER = ["COMMON", "UNCOMMON", "RARE", "GLORIOUS"]
RARITY_TARGETS = {"COMMON": 40, "UNCOMMON": 35, "RARE": 15, "GLORIOUS": 10}  # percentages

TYPE_ORDER = ["NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE"]
TYPE_TARGETS = {"NOUN": 16, "VERB": 20, "ADJECTIVE": 20, "NAME": 16, "TITLE": 18}  # counts for 90-card set


def _get_subtype_template(subtype: str) -> Path | None:
    """Get the template path for a specific subtype (rarity or type).

    Checks versioned template folders for matching subtype templates.
    Subtypes: common, uncommon, rare, glorious, noun, name, adjective, verb, title

    Returns:
        Path to template image if exists, None otherwise.
    """
    if not _CARD_TEMPLATE_DIR.exists():
        return None

    # Get current version from meta.yml
    meta_path = _CARD_TEMPLATE_DIR / "meta.yml"
    version = 1
    if meta_path.exists():
        try:
            import yaml
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = yaml.safe_load(f) or {}
            version = int(meta.get("version", 1))
        except (ValueError, TypeError):
            version = 1

    # Check for subtype template in versioned folder
    subtype_lower = subtype.lower()
    template_path = _CARD_TEMPLATE_DIR / f"v{version:03d}" / subtype_lower / "template_1024x1536.png"

    if template_path.exists():
        return template_path

    # Fallback to v001 if current version doesn't have the template
    fallback_path = _CARD_TEMPLATE_DIR / "v001" / subtype_lower / "template_1024x1536.png"
    if fallback_path.exists():
        return fallback_path

    return None


def _load_series_stats(series_dir: Path) -> dict:
    """Load series stats from stats.yml."""
    stats_path = series_dir / "stats.yml"
    if not stats_path.exists() or yaml is None:
        return {
            "rarity_counts": {r: 0 for r in RARITY_ORDER},
            "rarity_targets": RARITY_TARGETS,
            "type_counts": {t: 0 for t in TYPE_ORDER},
            "type_targets": TYPE_TARGETS,
            "total": 0,
        }

    with open(stats_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Handle both old format ("counts"/"targets") and new format ("rarity_counts"/"rarity_targets")
    rarity_counts = data.get("rarity_counts", data.get("counts", {}))
    for r in RARITY_ORDER:
        rarity_counts.setdefault(r, 0)

    type_counts = data.get("type_counts", {})
    for t in TYPE_ORDER:
        type_counts.setdefault(t, 0)

    return {
        "rarity_counts": rarity_counts,
        "rarity_targets": data.get("rarity_targets", data.get("targets", RARITY_TARGETS)),
        "type_counts": type_counts,
        "type_targets": data.get("type_targets", TYPE_TARGETS),
        "total": data.get("total", sum(rarity_counts.values())),
    }


def _save_series_stats(series_dir: Path, stats: dict) -> None:
    """Save series stats to stats.yml. Preserves theme if present."""
    if yaml is None:
        return
    stats_path = series_dir / "stats.yml"

    # Load existing data to preserve theme and other fields
    existing = {}
    if stats_path.exists():
        with open(stats_path, "r", encoding="utf-8") as f:
            existing = yaml.safe_load(f) or {}

    data = {
        "series": series_dir.name,
        "theme": existing.get("theme", ""),
        "cycle_days": 90,
        "start_date": existing.get("start_date", "2026-01-01"),
        "rarity_targets": stats.get("rarity_targets", RARITY_TARGETS),
        "type_targets": stats.get("type_targets", TYPE_TARGETS),
        "rarity_counts": stats["rarity_counts"],
        "type_counts": stats["type_counts"],
        "total": stats["total"],
    }

    with open(stats_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


# --------------------------------------------------------------------------
# Cards Index Tracking (git-compatible YAML-based tracking)
# --------------------------------------------------------------------------

def _load_cards_index(series_dir: Path) -> dict:
    """Load the cards index from cards_index.yml.

    The index tracks:
    - words: list of all words used in the series
    - abilities: list of ability pattern summaries
    - cards: list of card metadata (number, word, type, rarity, ability_summary)
    """
    index_path = series_dir / "cards_index.yml"
    if not index_path.exists() or yaml is None:
        return {
            "words": [],
            "ability_patterns": [],
            "cards": [],
        }

    with open(index_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return {
        "words": data.get("words", []),
        "ability_patterns": data.get("ability_patterns", []),
        "cards": data.get("cards", []),
    }


def _save_cards_index(series_dir: Path, index: dict) -> None:
    """Save the cards index to cards_index.yml."""
    if yaml is None:
        return

    index_path = series_dir / "cards_index.yml"

    data = {
        "words": sorted(set(str(w).upper() for w in index.get("words", []))),
        "ability_patterns": sorted(set(index.get("ability_patterns", []))),
        "cards": index.get("cards", []),
    }

    with open(index_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def _extract_ability_pattern(ability_text: str) -> str:
    """Extract a normalized ability pattern for tracking duplicates.

    Returns a simplified pattern like:
    - "look_top_add"
    - "discard_draw"
    - "type_effect_noun"
    - "stat_effect_lore"
    """
    if not ability_text:
        return ""

    text = ability_text.lower()
    patterns = []

    # Check for common mechanics
    if "look at" in text and "top" in text:
        patterns.append("look_top")
    if "add" in text and "hand" in text:
        patterns.append("add_hand")
    if "discard" in text:
        patterns.append("discard")
    if "draw" in text:
        patterns.append("draw")
    if "sheol" in text:
        patterns.append("sheol")
    if "pages" in text:
        patterns.append("pages")
    if "tower" in text:
        patterns.append("tower")

    # Check for type references
    for card_type in ["noun", "verb", "adjective", "name", "title"]:
        if card_type in text:
            patterns.append(f"type_{card_type}")
            break

    # Check for stat references
    for stat in ["lore", "context", "complexity"]:
        if stat in text:
            patterns.append(f"stat_{stat}")
            break

    # Check for conditional triggers
    if "when" in text or "if" in text:
        patterns.append("conditional")
    if "opponent" in text:
        patterns.append("opponent")
    if "choose" in text or "select" in text:
        patterns.append("choice")

    return "_".join(sorted(patterns)) if patterns else "unique"


def _add_card_to_index(
    series_dir: Path,
    *,
    number: int,
    word: str,
    card_type: str,
    rarity: str,
    ability_text: str,
) -> None:
    """Add a card to the series index for tracking."""
    index = _load_cards_index(series_dir)

    word_upper = word.upper()
    if word_upper not in index["words"]:
        index["words"].append(word_upper)

    ability_pattern = _extract_ability_pattern(ability_text)
    if ability_pattern and ability_pattern not in index["ability_patterns"]:
        index["ability_patterns"].append(ability_pattern)

    # Add card entry
    card_entry = {
        "number": number,
        "word": word_upper,
        "type": card_type.upper(),
        "rarity": rarity.upper(),
        "ability_pattern": ability_pattern,
    }

    # Check if card already exists (by number) and update if so
    existing_idx = None
    for i, c in enumerate(index["cards"]):
        if c.get("number") == number:
            existing_idx = i
            break

    if existing_idx is not None:
        index["cards"][existing_idx] = card_entry
    else:
        index["cards"].append(card_entry)

    _save_cards_index(series_dir, index)


def _get_existing_words_from_index(series_dir: Path) -> list[str]:
    """Get list of words already used in the series."""
    index = _load_cards_index(series_dir)
    return [w.upper() for w in index.get("words", [])]


def _get_existing_ability_patterns(series_dir: Path) -> list[str]:
    """Get list of ability patterns already used in the series."""
    index = _load_cards_index(series_dir)
    return index.get("ability_patterns", [])


def _rebuild_cards_index(series_dir: Path) -> dict:
    """Rebuild the cards index by scanning existing card directories.

    This is useful for initializing the index from existing cards or
    recovering from a corrupted index file.

    Handles both structures:
    - series_dir/cards/001-word/  (main series)
    - series_dir/001-word/  (demo cards)
    """
    if yaml is None:
        return {"words": [], "ability_patterns": [], "cards": []}

    # Try series_dir/cards first, then series_dir itself
    cards_dir = series_dir / "cards"
    if not cards_dir.exists():
        cards_dir = series_dir
    if not cards_dir.exists():
        return {"words": [], "ability_patterns": [], "cards": []}

    words: list[str] = []
    ability_patterns: list[str] = []
    cards: list[dict] = []

    for card_path in sorted(cards_dir.iterdir()):
        if not card_path.is_dir():
            continue

        meta_file = card_path / "meta.yml"
        if not meta_file.exists():
            continue

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = yaml.safe_load(f) or {}
        except Exception:
            continue

        word = str(meta.get("word", "")).upper()
        if not word:
            continue

        number_str = meta.get("number", "")
        try:
            number = int(number_str)
        except (ValueError, TypeError):
            # Try to extract from directory name
            try:
                number = int(card_path.name.split("-")[0])
            except (ValueError, IndexError):
                continue

        card_type = str(meta.get("card_type", "NOUN")).upper()
        rarity = str(meta.get("rarity", "COMMON")).upper()
        ability_text = str(meta.get("ability", ""))

        words.append(word)
        pattern = _extract_ability_pattern(ability_text)
        if pattern:
            ability_patterns.append(pattern)

        cards.append({
            "number": number,
            "word": word,
            "type": card_type,
            "rarity": rarity,
            "ability_pattern": pattern,
        })

    index = {
        "words": sorted(set(words)),
        "ability_patterns": sorted(set(ability_patterns)),
        "cards": cards,
    }

    _save_cards_index(series_dir, index)
    return index


def _get_needed_rarity(stats: dict) -> str:
    """Determine which rarity is most under-represented vs targets (percentage-based)."""
    counts = stats["rarity_counts"]
    targets = stats.get("rarity_targets", RARITY_TARGETS)
    total = max(stats["total"], 1)

    # Calculate deficit: target% - current%
    deficits = {}
    for rarity in RARITY_ORDER:
        current_pct = (counts.get(rarity, 0) / total) * 100
        target_pct = targets.get(rarity, 25)
        deficits[rarity] = target_pct - current_pct

    # Return rarity with highest deficit
    return max(deficits, key=deficits.get)


def _get_needed_type(stats: dict) -> str:
    """Determine which card type is most under-represented vs targets (count-based)."""
    counts = stats["type_counts"]
    targets = stats.get("type_targets", TYPE_TARGETS)

    # Calculate deficit: target_count - current_count
    deficits = {}
    for card_type in TYPE_ORDER:
        current = counts.get(card_type, 0)
        target = targets.get(card_type, 18)
        deficits[card_type] = target - current

    # Return type with highest deficit
    return max(deficits, key=deficits.get)


def _get_card_rarity(card_img_path: Path) -> str | None:
    """Get the rarity of a card from its meta.yml."""
    # card_img_path is like .../cards/word/outputs/card_1024x1536.png
    card_dir = card_img_path.parent.parent
    meta_file = card_dir / "meta.yml"
    if not meta_file.exists():
        return None
    try:
        with open(meta_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("rarity:"):
                    return line.split(":", 1)[1].strip().upper()
    except OSError:
        pass
    return None


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


def _find_matching_cards(
    series_root: Path,
    target_rarity: str | None = None,
    target_type: str | None = None,
    exclude_card: Path | None = None,
    max_cards: int = 3,
) -> list[Path]:
    """Find cards matching rarity and/or type.

    Args:
        series_root: Series directory containing cards/
        target_rarity: Rarity to match (e.g., "RARE")
        target_type: Card type to match (e.g., "NOUN", "VERB")
        exclude_card: Card directory to exclude (the card being fixed)
        max_cards: Maximum number of cards to return

    Returns:
        List of paths to matching card images.
    """
    cards_dir = series_root / "cards"
    if not cards_dir.exists():
        # Try demo_cards structure
        if series_root.name == "demo_cards" or "demo_cards" in str(series_root):
            cards_dir = series_root
        else:
            return []

    matches: list[Path] = []

    for card_dir in sorted(cards_dir.iterdir()):
        if not card_dir.is_dir():
            continue
        if exclude_card and card_dir.resolve() == exclude_card.resolve():
            continue

        meta_file = card_dir / "meta.yml"
        img_file = card_dir / "outputs" / "card_1024x1536.png"
        if not img_file.exists():
            continue

        # Check rarity and type from meta.yml
        card_rarity = None
        card_type = None

        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("rarity:"):
                            card_rarity = line.split(":", 1)[1].strip().upper()
                        elif line.startswith("card_type:"):
                            card_type = line.split(":", 1)[1].strip().upper()
            except OSError:
                continue

        # Also check card.json for type if not in meta
        if card_type is None:
            card_json = card_dir / "card.json"
            if card_json.exists():
                try:
                    card_data = read_json(card_json)
                    card_type = card_data.get("content", {}).get("TYPE", "").upper()
                    if not card_rarity:
                        card_rarity = card_data.get("content", {}).get("RARITY_TEXT", "").upper()
                except Exception:
                    pass

        # Check if matches criteria
        rarity_match = (target_rarity is None) or (card_rarity == target_rarity.upper())
        type_match = (target_type is None) or (card_type == target_type.upper())

        if rarity_match and type_match:
            matches.append(img_file)
            if len(matches) >= max_cards:
                break

    return matches


def _get_series_theme(series_dir: Path) -> str:
    """Get the series theme/set name (e.g., 'Babel')."""
    stats_file = series_dir / "stats.yml"
    if stats_file.exists() and yaml:
        with open(stats_file, "r", encoding="utf-8") as f:
            stats = yaml.safe_load(f) or {}
        return stats.get("theme", "").strip()
    return ""


def _get_series_display_name(series_dir: Path) -> str:
    """Get series display name including theme (e.g., '2026-Q1 Babel')."""
    series_name = series_dir.name
    theme = _get_series_theme(series_dir)
    if theme:
        return f"{series_name} {theme}"
    return series_name


def _build_style_refs(
    series_root: Path,
    *,
    current_card_path: Path | None = None,
    target_rarity: str | None = None,
    target_type: str | None = None,
    fix_mode: bool = False,
    templates_only: bool = False,
) -> tuple[list[str], dict[int, str], bool]:
    """Build list of style reference paths for image generation.

    For fix_mode=True (revise/polish):
        [1] = Current card being fixed
        [2] = Template
        [3+] = Example cards

    For fix_mode=False (rebuild/generate):
        [1] = Template
        [2+] = Example cards

    Example card selection priority (fills up to 3 cards):
        1. Same rarity + same type
        2. Same rarity only
        3. Same type only (tracks actual rarity for PRIMARY highlighting)
        4. Any cards from series (tracks actual rarity)

    Args:
        series_root: Series directory for finding example cards.
        current_card_path: Path to current card image (for fix mode).
        target_rarity: Target rarity to match.
        target_type: Target type to match.
        fix_mode: If True, includes current card as first reference.
        templates_only: If True, skip series cards and only use templates + example cards.

    Returns:
        Tuple of (refs list, rarity_labels dict mapping position to rarity, fix_mode flag)
    """
    refs: list[str] = []
    rarity_labels: dict[int, str] = {}

    # For fix mode, current card comes first
    if fix_mode and current_card_path and current_card_path.exists():
        refs.append(str(current_card_path))

    # Collect type and rarity templates for later (added last as weakest refs)
    type_template_path: Path | None = None
    rarity_template_path: Path | None = None
    if target_type:
        type_template_path = _get_subtype_template(target_type)
    if target_rarity:
        rarity_template_path = _get_subtype_template(target_rarity)

    # For templates_only mode, collect example cards sorted by similarity
    # Examples are now the STRONGEST references (positions 1-3)
    example_refs: list[tuple[Path, str]] = []  # [(path, rarity), ...]

    if templates_only:
        example_cards_dir = Path("templates/example_cards")
        if example_cards_dir.exists():
            # Collect all completed example cards with their metadata
            available_examples: list[tuple[Path, str, str]] = []  # (path, type, rarity)
            for card_dir in sorted(example_cards_dir.iterdir()):
                if not card_dir.is_dir():
                    continue
                card_png = card_dir / "outputs" / "card_1024x1536.png"
                if not card_png.exists():
                    continue
                # Skip the card we're currently generating
                if current_card_path and card_png.resolve() == current_card_path.resolve():
                    continue
                # Get metadata
                meta_path = card_dir / "meta.yml"
                card_type_meta = ""
                card_rarity_meta = ""
                if meta_path.exists() and yaml:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = yaml.safe_load(f) or {}
                    card_type_meta = (meta.get("card_type") or meta.get("type", "")).upper()
                    card_rarity_meta = meta.get("rarity", "").upper()
                available_examples.append((card_png, card_type_meta, card_rarity_meta))

            # Sort by overall similarity (type + rarity) to find best match
            def overall_similarity(item: tuple[Path, str, str]) -> int:
                _, ex_type, ex_rarity = item
                score = 0
                if target_type and ex_type == target_type:
                    score += 2  # Type match
                if target_rarity and ex_rarity == target_rarity:
                    score += 2  # Rarity match (equal weight for best match)
                return -score  # Negative for descending sort

            available_examples.sort(key=overall_similarity)

            # Best match is first, then sort rest by rarity priority
            if available_examples:
                example_refs.append((available_examples[0][0], available_examples[0][2]))

                # For remaining examples, prioritize RARITY match, type secondary
                rest = available_examples[1:]
                def rarity_first(item: tuple[Path, str, str]) -> tuple[int, int]:
                    _, ex_type, ex_rarity = item
                    rarity_score = 2 if (target_rarity and ex_rarity == target_rarity) else 0
                    type_score = 1 if (target_type and ex_type == target_type) else 0
                    return (-rarity_score, -type_score)  # Negative for descending

                rest.sort(key=rarity_first)
                for card_png, _, card_rarity_meta in rest[:2]:
                    example_refs.append((card_png, card_rarity_meta))

    # Style refs ordered by priority (earlier = stronger weight in Gemini):
    # 1-3. Example cards (strongest - real completed cards)
    for card_png, card_rarity_meta in example_refs:
        refs.append(str(card_png))
        if card_rarity_meta:
            rarity_labels[len(refs)] = card_rarity_meta

    # 4. Type template (weaker - just for type icon reference)
    if type_template_path:
        refs.append(str(type_template_path))

    # 5. Rarity template (weakest - just for rarity badge reference)
    if rarity_template_path:
        refs.append(str(rarity_template_path))

    # Skip series cards if templates_only mode (for example cards)
    if not templates_only:
        # Find matching cards (same rarity+type)
        exclude_dir = current_card_path.parent.parent if current_card_path else None
        matching_cards = _find_matching_cards(
            series_root,
            target_rarity=target_rarity,
            target_type=target_type,
            exclude_card=exclude_dir,
            max_cards=3,
        )

        # If not enough matches, try same rarity only
        if len(matching_cards) < 3 and target_rarity:
            more_cards = _find_matching_cards(
                series_root,
                target_rarity=target_rarity,
                target_type=None,
                exclude_card=exclude_dir,
                max_cards=3 - len(matching_cards),
            )
            for card in more_cards:
                if card not in matching_cards:
                    matching_cards.append(card)

        # Track actual rarities for cards that don't match target_rarity
        fallback_rarities: dict[Path, str] = {}

        # If still not enough, try same type only (these may have different rarities)
        if len(matching_cards) < 3 and target_type:
            more_cards = _find_matching_cards(
                series_root,
                target_rarity=None,
                target_type=target_type,
                exclude_card=exclude_dir,
                max_cards=3 - len(matching_cards),
            )
            for card in more_cards:
                if card not in matching_cards:
                    matching_cards.append(card)
                    # Track actual rarity since it may differ from target
                    actual_rarity = _get_card_rarity(card)
                    if actual_rarity:
                        fallback_rarities[card] = actual_rarity

        # If still not enough, fill with any cards from the series
        if len(matching_cards) < 3:
            rarity_map = _find_card_by_rarity(series_root)
            for rarity in RARITY_ORDER:
                if rarity in rarity_map:
                    card_path = rarity_map[rarity]
                    if card_path not in matching_cards:
                        matching_cards.append(card_path)
                        fallback_rarities[card_path] = rarity
                        if len(matching_cards) >= 3:
                            break

        for card_path in matching_cards:
            refs.append(str(card_path))
            # Use actual rarity for fallback cards, target_rarity for matched cards
            if card_path in fallback_rarities:
                rarity_labels[len(refs)] = fallback_rarities[card_path]
            elif target_rarity:
                rarity_labels[len(refs)] = target_rarity

    return refs, rarity_labels, fix_mode


def _build_style_cmd_args(
    style_refs: list[str],
    rarity_labels: dict[int, str] | None = None,
    target_rarity: str | None = None,
    fix_mode: bool = False,
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

    if fix_mode:
        args.append("--fix-mode")

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


# Era/theme descriptions for constraining word selection
SERIES_THEME_PROMPTS = {
    "Babel": (
        "SERIES THEME: Babel (Pre-Abraham Era, Genesis 1-11)\n\n"
        "RARITY CONSTRAINTS:\n"
        "- COMMON & UNCOMMON: Any Biblical word that has both Greek and Hebrew equivalents. "
        "These are general vocabulary cards.\n"
        "- RARE & GLORIOUS: MUST be specific to the Pre-Abraham era (Genesis 1-11). "
        "Words relevant to: Creation, Eden, the Fall, Cain & Abel, the Flood, Noah, "
        "the Tower of Babel, early humanity, origins, divine names, and primordial concepts. "
        "Examples: EDEN, SERPENT, TREE, CURSE, BLOOD, FLOOD, ARK, COVENANT, BABEL, TONGUE, SCATTER, "
        "ADAM, EVE, CAIN, ABEL, NOAH, NEPHILIM, NIMROD, CREATE, FALL, SIN, DEATH, LIFE.\n\n"
        "All words MUST have both Greek (NT/LXX) and Hebrew (OT) forms."
    ),
    "Egypt": (
        "SERIES THEME: Egypt (Patriarchs to Exodus)\n\n"
        "RARITY CONSTRAINTS:\n"
        "- COMMON & UNCOMMON: Any Biblical word that has both Greek and Hebrew equivalents.\n"
        "- RARE & GLORIOUS: MUST be specific to the Egyptian era (Genesis 37 - Exodus). "
        "Words relevant to: Joseph, slavery, Pharaoh, plagues, Moses, deliverance, Passover, "
        "the wilderness, and God's mighty acts against Egypt.\n\n"
        "All words MUST have both Greek (NT/LXX) and Hebrew (OT) forms."
    ),
    "Israel": (
        "SERIES THEME: Israel (Conquest to United Kingdom)\n\n"
        "RARITY CONSTRAINTS:\n"
        "- COMMON & UNCOMMON: Any Biblical word that has both Greek and Hebrew equivalents.\n"
        "- RARE & GLORIOUS: MUST be specific to the Israelite era (Joshua - Solomon). "
        "Words relevant to: conquest, judges, kings, the united kingdom, temple, "
        "David, Solomon, worship, and the promised land.\n\n"
        "All words MUST have both Greek (NT/LXX) and Hebrew (OT) forms."
    ),
}


def _generate_queue_entries(
    *,
    count: int,
    existing_words: list[str],
    needed_rarities: list[str] | None = None,
    needed_types: list[str] | None = None,
    series_dir: Path | None = None,
) -> list[dict]:
    # Get theme constraint if series_dir provided
    theme_instruction = ""
    if series_dir and yaml:
        stats_file = series_dir / "stats.yml"
        if stats_file.exists():
            with open(stats_file, "r", encoding="utf-8") as f:
                stats = yaml.safe_load(f) or {}
            theme = stats.get("theme", "").strip()
            if theme and theme in SERIES_THEME_PROMPTS:
                theme_instruction = SERIES_THEME_PROMPTS[theme] + "\n\n"

    # Build specific assignments if we have both types and rarities
    specific_assignments = ""
    if needed_rarities and needed_types and len(needed_rarities) == count and len(needed_types) == count:
        assignments = []
        for i, (rarity, card_type) in enumerate(zip(needed_rarities, needed_types), 1):
            assignments.append(f"  Entry {i}: card_type={card_type}, rarity={rarity}")
        specific_assignments = (
            "REQUIRED ASSIGNMENTS (you MUST follow these exactly):\n"
            + "\n".join(assignments)
            + "\n\n"
        )

    # Build rarity instruction based on what's needed
    if needed_rarities and not specific_assignments:
        rarity_instruction = (
            f"IMPORTANT: The series needs these rarities most urgently: {', '.join(needed_rarities)}. "
            f"Assign the FIRST entry rarity={needed_rarities[0]}. "
            "Distribute remaining entries to help balance the set."
        )
    elif not specific_assignments:
        rarity_instruction = (
            "IMPORTANT: Distribute rarities to form a balanced set "
            "(approx. 10% GLORIOUS, 15% RARE, 35% UNCOMMON, 40% COMMON)."
        )
    else:
        rarity_instruction = ""

    # Build type instruction if needed (without specific assignments)
    if needed_types and not specific_assignments:
        type_instruction = (
            f"IMPORTANT: The series needs these types most urgently: {', '.join(needed_types)}. "
            f"Assign the FIRST entry card_type={needed_types[0]}. "
        )
    elif not specific_assignments:
        type_instruction = (
            "Distribute types to form a balanced set "
            "(approx. NOUN:18%, VERB:22%, ADJECTIVE:22%, NAME:18%, TITLE:20%)."
        )
    else:
        type_instruction = ""

    # Rarity-weight guidance: match word importance to rarity
    rarity_weight_guide = (
        "RARITY MUST MATCH WORD IMPORTANCE:\n"
        "- GLORIOUS: Central theological terms, divine names, pivotal narrative words "
        "(e.g., MESSIAH, YAHWEH, RESURRECTION, COVENANT, GLORY, REDEEM)\n"
        "- RARE: Significant theological concepts, major figures, key events "
        "(e.g., PROPHET, KING, TEMPLE, SACRIFICE, MIRACLE, APOSTLE)\n"
        "- UNCOMMON: Important but more common biblical vocabulary "
        "(e.g., PRAY, BLESS, FAITH, SERVANT, SHEPHERD, WITNESS)\n"
        "- COMMON: Everyday biblical words, simple concepts "
        "(e.g., WALK, HEAR, BREAD, WATER, HOUSE, STONE)\n\n"
        "Pick words that FIT the assigned rarity. Don't assign KING as COMMON or WATER as GLORIOUS.\n\n"
    )

    prompt = (
        theme_instruction
        + rarity_weight_guide
        + specific_assignments
        + "Generate "
        + str(count)
        + " distinct English words for a daily Biblical word-study trading card project. "
        "Avoid any words already used: "
        + (", ".join(existing_words) if existing_words else "none")
        + ". "
        "For each item, provide: card_type (NOUN|VERB|ADJECTIVE|NAME|TITLE) and rarity (COMMON|UNCOMMON|RARE|GLORIOUS). "
        + rarity_instruction + " " + type_instruction + " "
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
        "  \"trivia\": [exactly 3 short strings]\n"
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
    if len(cleaned) > 3:
        cleaned = cleaned[:3]
    return cleaned


def _pick_demo_entry(demo_dir: Path | None = None) -> dict:
    """Pick a random word/type/rarity for a demo card, avoiding existing words."""
    existing_words: list[str] = []

    # Collect existing words from demo_cards
    if demo_dir and demo_dir.exists():
        for card_dir in demo_dir.iterdir():
            if not card_dir.is_dir():
                continue
            card_json = card_dir / "card.json"
            if card_json.exists():
                try:
                    card = read_json(card_json)
                    word = card.get("content", {}).get("WORD", "").strip().upper()
                    if word:
                        existing_words.append(word)
                except Exception:
                    pass
            else:
                # Try to extract word from folder name (e.g., "143-moses" -> "MOSES")
                parts = card_dir.name.split("-", 1)
                if len(parts) > 1:
                    existing_words.append(parts[1].upper())

    candidates = _generate_queue_entries(count=5, existing_words=existing_words)
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


class ReviseFormResult:
    """Result from parsing a revise.txt form."""
    def __init__(
        self,
        instructions: str,
        allowed_paths: set[str],
        rebuild: bool = False,
        card_changes: dict[str, tuple[str, str]] | None = None,
    ):
        self.instructions = instructions
        self.allowed_paths = allowed_paths
        self.rebuild = rebuild
        # card_changes maps field name -> (old_value, new_value)
        self.card_changes = card_changes or {}


# Mapping from Card_* fields in revise.txt to card.json content paths
_CARD_PREVIEW_FIELDS = {
    "Card_Word": "WORD",
    "Card_Gloss": "GLOSS",
    "Card_Type": "CARD_TYPE",
    "Card_Rarity": "RARITY_TEXT",
    "Card_Ability": "ABILITY_TEXT",
    "Card_Art_Prompt": "ART_PROMPT",
}


def _parse_revise_form(raw: str, card: dict | None = None) -> ReviseFormResult:
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

    rebuild = False
    current_key: str | None = None
    rarity_lines: list[str] = []
    ability_lines: list[str] = []
    stats_lines: list[str] = []
    general_lines: list[str] = []
    card_preview_values: dict[str, str] = {}

    for line in raw.splitlines():
        stripped = line.strip()

        # Skip comments (but Card_ fields in comments are intentional)
        if line.lstrip().startswith("#") and not stripped.startswith("# Card_"):
            continue

        # Parse Rebuild field
        if line.startswith("Rebuild:"):
            val = line.split(":", 1)[1].strip().lower()
            rebuild = val in ("true", "yes", "1")
            continue

        # Parse Card_ preview fields (they appear as comments: # Card_Word: value)
        for prefix in ("# Card_", "Card_"):
            if stripped.startswith(prefix):
                rest = stripped[len(prefix):]
                if ":" in rest:
                    field_name, value = rest.split(":", 1)
                    field_key = f"Card_{field_name.strip()}"
                    value = value.strip()
                    if not is_placeholder(value):
                        card_preview_values[field_key] = value
                break

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

    # Detect changes in Card_ preview fields
    card_changes: dict[str, tuple[str, str]] = {}
    if card is not None:
        content = card.get("content", {})
        for preview_field, json_field in _CARD_PREVIEW_FIELDS.items():
            if preview_field in card_preview_values:
                new_val = card_preview_values[preview_field]
                old_val = str(content.get(json_field, ""))
                if new_val != old_val:
                    card_changes[json_field] = (old_val, new_val)

        # Handle Card_Stats specially: "LORE 3 | CONTEXT 4 | COMPLEXITY 2"
        if "Card_Stats" in card_preview_values:
            stats_str = card_preview_values["Card_Stats"]
            import re
            lore_match = re.search(r"LORE\s*(\d+)", stats_str, re.IGNORECASE)
            context_match = re.search(r"CONTEXT\s*(\d+)", stats_str, re.IGNORECASE)
            complexity_match = re.search(r"COMPLEXITY\s*(\d+)", stats_str, re.IGNORECASE)
            if lore_match:
                new_val = int(lore_match.group(1))
                old_val = content.get("STAT_LORE", 0)
                if new_val != old_val:
                    card_changes["STAT_LORE"] = (str(old_val), str(new_val))
            if context_match:
                new_val = int(context_match.group(1))
                old_val = content.get("STAT_CONTEXT", 0)
                if new_val != old_val:
                    card_changes["STAT_CONTEXT"] = (str(old_val), str(new_val))
            if complexity_match:
                new_val = int(complexity_match.group(1))
                old_val = content.get("STAT_COMPLEXITY", 0)
                if new_val != old_val:
                    card_changes["STAT_COMPLEXITY"] = (str(old_val), str(new_val))

        # Handle verse fields: "Card_OT_Verse: REF — SNIPPET"
        if "Card_OT_Verse" in card_preview_values:
            verse_str = card_preview_values["Card_OT_Verse"]
            if "—" in verse_str:
                ref, snippet = verse_str.split("—", 1)
                ref = ref.strip()
                snippet = snippet.strip()
                old_ref = content.get("OT_VERSE_REF", "")
                old_snippet = content.get("OT_VERSE_SNIPPET", "")
                if ref != old_ref:
                    card_changes["OT_VERSE_REF"] = (old_ref, ref)
                if snippet != old_snippet:
                    card_changes["OT_VERSE_SNIPPET"] = (old_snippet, snippet)

        if "Card_NT_Verse" in card_preview_values:
            verse_str = card_preview_values["Card_NT_Verse"]
            if "—" in verse_str:
                ref, snippet = verse_str.split("—", 1)
                ref = ref.strip()
                snippet = snippet.strip()
                old_ref = content.get("NT_VERSE_REF", "")
                old_snippet = content.get("NT_VERSE_SNIPPET", "")
                if ref != old_ref:
                    card_changes["NT_VERSE_REF"] = (old_ref, ref)
                if snippet != old_snippet:
                    card_changes["NT_VERSE_SNIPPET"] = (old_snippet, snippet)

        # Handle Hebrew/Greek: "Card_Hebrew: רָאָה (Ra'ah)"
        if "Card_Hebrew" in card_preview_values:
            heb_str = card_preview_values["Card_Hebrew"]
            if "(" in heb_str and ")" in heb_str:
                heb = heb_str[:heb_str.index("(")].strip()
                translit = heb_str[heb_str.index("(")+1:heb_str.index(")")].strip()
                old_heb = content.get("HEBREW", "")
                old_translit = content.get("HEBREW_TRANSLIT", "")
                if heb != old_heb:
                    card_changes["HEBREW"] = (old_heb, heb)
                if translit != old_translit:
                    card_changes["HEBREW_TRANSLIT"] = (old_translit, translit)

        if "Card_Greek" in card_preview_values:
            greek_str = card_preview_values["Card_Greek"]
            if "(" in greek_str and ")" in greek_str:
                greek = greek_str[:greek_str.index("(")].strip()
                translit = greek_str[greek_str.index("(")+1:greek_str.index(")")].strip()
                old_greek = content.get("GREEK", "")
                old_translit = content.get("GREEK_TRANSLIT", "")
                if greek != old_greek:
                    card_changes["GREEK"] = (old_greek, greek)
                if translit != old_translit:
                    card_changes["GREEK_TRANSLIT"] = (old_translit, translit)

        # Handle trivia bullets
        trivia_bullets = content.get("TRIVIA_BULLETS", [])
        for i in range(1, 5):
            key = f"Card_Trivia_{i}"
            if key in card_preview_values:
                new_val = card_preview_values[key]
                old_val = trivia_bullets[i-1] if i <= len(trivia_bullets) else ""
                if new_val != old_val:
                    card_changes[f"TRIVIA_{i}"] = (old_val, new_val)

    allowed_paths: set[str] = set()
    if rarity_req:
        allowed_paths.update({"/content/RARITY_TEXT", "/content/RARITY_ICON"})
    if ability_req:
        allowed_paths.add("/content/ABILITY_TEXT")
    if stats_req:
        allowed_paths.update({"/content/STAT_LORE", "/content/STAT_CONTEXT", "/content/STAT_COMPLEXITY"})
    if general_req or card_changes:
        # General revision or card preview changes unlock ALL content fields plus model_prompt
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

    # Return early if nothing to do (but rebuild alone is valid)
    if not allowed_paths and not rebuild:
        return ReviseFormResult("", set(), rebuild=False, card_changes={})

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

    # Add card preview changes to instructions
    if card_changes:
        if out_lines:
            out_lines.append("")
        out_lines.append("Card field changes (from preview):")
        for field, (old_val, new_val) in card_changes.items():
            out_lines.append(f"  {field}: '{old_val}' -> '{new_val}'")

    return ReviseFormResult(
        "\n".join(out_lines).strip(),
        allowed_paths,
        rebuild=rebuild,
        card_changes=card_changes,
    )


def _build_revise_content(card: dict) -> str:
    """Build the content of revise.txt with current card data populated."""
    content = card.get("content", {})

    # Get trivia bullets
    trivia = content.get("TRIVIA_BULLETS", [])
    trivia_1 = trivia[0] if len(trivia) > 0 else ""
    trivia_2 = trivia[1] if len(trivia) > 1 else ""
    trivia_3 = trivia[2] if len(trivia) > 2 else ""

    lines = [
        "# Hypertext Card Revision Form (revise.txt)",
        "#",
        "# Edit this file in your PR branch, then run the \"Revise Hypertext Card\" workflow.",
        "#",
        "# Options:",
        "# - Rebuild: Set to 'true' to regenerate the card image from scratch",
        "#   (useful when revisions aren't fixing stubborn visual issues)",
        "#",
        "# Specific fields for targeted changes:",
        "# - Rarity_Change_Request: changes rarity only",
        "# - Ability_Change_Request: changes ability only",
        "# - Stats_Change_Request: changes stats only",
        "#",
        "# General_Revision_Request: unlocks ALL content fields for broad revisions",
        "# (art prompt, gloss, verses, trivia, Greek/Hebrew, etc.)",
        "#",
        "# Card Preview: Shows current card data. Edit values directly to request changes.",
        "# The system will detect your edits and apply them automatically.",
        "#",
        "# Notes:",
        "# - Leave a field blank to keep it unchanged.",
        "# - Lines starting with # are ignored (except Card_ fields below).",
        "",
        "Rebuild: false",
        "",
        "Rarity_Change_Request: <leave blank unless changing rarity>",
        "",
        "Ability_Change_Request: <describe the new ability; avoid saying \"your deck\"; say \"the deck\" or \"the shared deck\">",
        "",
        "Stats_Change_Request: <optional; if changing, specify LORE/CONTEXT/COMPLEXITY targets>",
        "",
        "General_Revision_Request: <describe any changes; unlocks all fields: art, gloss, verses, trivia, etc.>",
        "",
        "# ─────────────────────────────────────────────────────────────────────────────",
        "# CURRENT CARD (edit values below to request changes)",
        "# ─────────────────────────────────────────────────────────────────────────────",
        "#",
        f"# Card_Word: {content.get('WORD', '')}",
        f"# Card_Gloss: {content.get('GLOSS', '')}",
        f"# Card_Type: {content.get('CARD_TYPE', '')}",
        f"# Card_Rarity: {content.get('RARITY_TEXT', '')}",
        f"# Card_Ability: {content.get('ABILITY_TEXT', '')}",
        f"# Card_Stats: LORE {content.get('STAT_LORE', 0)} | CONTEXT {content.get('STAT_CONTEXT', 0)} | COMPLEXITY {content.get('STAT_COMPLEXITY', 0)}",
        f"# Card_Art_Prompt: {content.get('ART_PROMPT', '')}",
        f"# Card_OT_Verse: {content.get('OT_VERSE_REF', '')} — {content.get('OT_VERSE_SNIPPET', '')}",
        f"# Card_NT_Verse: {content.get('NT_VERSE_REF', '')} — {content.get('NT_VERSE_SNIPPET', '')}",
        f"# Card_Hebrew: {content.get('HEBREW', '')} ({content.get('HEBREW_TRANSLIT', '')})",
        f"# Card_Greek: {content.get('GREEK', '')} ({content.get('GREEK_TRANSLIT', '')})",
        f"# Card_Trivia_1: {trivia_1}",
        f"# Card_Trivia_2: {trivia_2}",
        f"# Card_Trivia_3: {trivia_3}",
    ]
    return "\n".join(lines) + "\n"


def _seed_revise_file(card_dir: Path, force: bool = False) -> None:
    """Seed or update revise.txt with current card data.

    Args:
        card_dir: Path to the card directory
        force: If True, regenerate even if file exists (to update card preview)
    """
    target = card_dir / "revise.txt"
    card_path = card_dir / "card.json"

    # If card.json exists, build revise.txt with current card data
    if card_path.exists():
        if target.exists() and not force:
            return
        card = read_json(card_path)
        target.write_text(_build_revise_content(card), encoding="utf-8")
        return

    # Fallback to template if no card.json
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

    # Normalize rarity (style references handle visual appearance)
    rarity = str(data.get("RARITY_TEXT", "COMMON")).upper()
    data["RARITY_TEXT"] = rarity
        
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
        # Combine words from queue AND from series index (for deduplication)
        queue_words = [str(x.get("word", "")).upper() for x in queue if isinstance(x, dict)]
        index_words = _get_existing_words_from_index(series_dir)
        existing_words = list(set(queue_words + index_words))
        _log(f"[plan] existing words (queue + index): {len(existing_words)} total")

        min_queue = int(os.environ.get("HYPERTEXT_MIN_QUEUE", "3"))
        if len(queue) < min_queue:
            needed = min_queue - len(queue)
            print(f"Queue below minimum ({len(queue)}/{min_queue}). Generating {needed} new queue entries...")

            # Calculate needed rarities and types from stats
            stats = _load_series_stats(series_dir)
            needed_rarities = []
            needed_types = []
            for _ in range(needed):
                nr = _get_needed_rarity(stats)
                nt = _get_needed_type(stats)
                needed_rarities.append(nr)
                needed_types.append(nt)
                stats["rarity_counts"][nr] = stats["rarity_counts"].get(nr, 0) + 1
                stats["type_counts"][nt] = stats["type_counts"].get(nt, 0) + 1
                stats["total"] += 1

            _log(f"[plan] needed rarities: {needed_rarities}")
            _log(f"[plan] needed types: {needed_types}")
            queue.extend(_generate_queue_entries(
                count=needed,
                existing_words=existing_words,
                needed_rarities=needed_rarities,
                needed_types=needed_types,
                series_dir=series_dir,
            ))
            save_queue(queue_path, queue)

    if not queue:
        print("Queue empty.")
        return 0

    print(f"Queue entries: {len(queue)}")

    # Find first queue entry that doesn't have a completed card
    entry = None
    number = 0
    for idx, q_entry in enumerate(queue):
        number = idx + 1  # 1-indexed card number from queue position
        word = str(q_entry.get("word", "")).upper()
        slug = slugify(word)
        card_dir = cards_dir / f"{number:03d}-{slug}"

        # Skip if card folder exists with completed output
        out_png = card_dir / "outputs" / "card_1024x1536.png"
        if out_png.exists():
            _log(f"[plan] skipping #{number:03d} {word} - already complete")
            continue

        # Found an incomplete entry
        entry = q_entry
        break

    if entry is None:
        print("All queue entries already have completed cards.")
        return 0

    word = str(entry["word"]).upper()
    slug = slugify(word)
    card_dir = cards_dir / f"{number:03d}-{slug}"

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
        card["content"]["SERIES"] = _get_series_display_name(series_dir)
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
            "series": series_dir.name,
            "set": _get_series_theme(series_dir),
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
        card["content"]["SERIES"] = _get_series_display_name(series_dir)
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

    # Queue entries are kept (not removed) - card number is based on queue position

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

    # Update series stats with both rarity and type
    stats = _load_series_stats(series_dir)
    stats["rarity_counts"][rarity] = stats["rarity_counts"].get(rarity, 0) + 1
    stats["type_counts"][card_type] = stats["type_counts"].get(card_type, 0) + 1
    stats["total"] = sum(stats["rarity_counts"].values())
    _save_series_stats(series_dir, stats)
    _log(f"[phase plan] updated stats.yml: {card_type}/{rarity}, total={stats['total']}")

    # Add card to series index for tracking
    ability_text = card["content"].get("ABILITY_TEXT", "")
    _add_card_to_index(
        series_dir,
        number=number,
        word=word,
        card_type=card_type,
        rarity=rarity,
        ability_text=ability_text,
    )
    _log(f"[phase plan] updated cards_index.yml")

    return 0


def _plan_demo_card_with_number(
    *,
    series_dir: Path,
    template_path: Path,
    demo_dir: Path,
    number: int,
    entry: dict,
    set_name: str = "Demo",
    series_display: str | None = None,
) -> Path | None:
    """Plan a single demo card with a pre-assigned number (for parallel execution).

    Args:
        series_display: Override for the SERIES field on the card (e.g., "Example" instead of "2026-Q1 Babel")

    Returns card_dir or None on failure.
    """
    if yaml is None:
        raise RuntimeError("pyyaml is required. Install with: pip install pyyaml")

    word = str(entry["word"]).upper()
    slug = slugify(word)
    card_type = str(entry.get("card_type", "NOUN")).strip().upper()
    rarity = str(entry.get("rarity", "COMMON")).strip().upper()

    _log(f"[demo plan] planning: #{number:03d} word={word} type={card_type} rarity={rarity}")

    card_dir = demo_dir / f"{number:03d}-{slug}"
    os.makedirs(card_dir, exist_ok=True)

    if not template_path.exists():
        print(f"Missing {template_path}")
        return None

    try:
        recipe = _generate_card_recipe(number=number, word=word, card_type=card_type, rarity=rarity)
    except Exception as e:
        _log(f"[demo plan] recipe generation failed for #{number:03d} {word}: {e}")
        return None

    grounding = recipe.get("grounding", {}) if isinstance(recipe.get("grounding"), dict) else {}
    stats = recipe.get("stats", {}) if isinstance(recipe.get("stats"), dict) else {}
    ot_verse = recipe.get("ot_verse", {}) if isinstance(recipe.get("ot_verse"), dict) else {}
    nt_verse = recipe.get("nt_verse", {}) if isinstance(recipe.get("nt_verse"), dict) else {}
    greek = recipe.get("greek", {}) if isinstance(recipe.get("greek"), dict) else {}
    hebrew = recipe.get("hebrew", {}) if isinstance(recipe.get("hebrew"), dict) else {}

    trivia = recipe.get("trivia", [])
    if not isinstance(trivia, list):
        trivia = []
    try:
        trivia_items = _normalize_trivia([str(x) for x in trivia])
    except Exception:
        trivia_items = ["Trivia item 1", "Trivia item 2", "Trivia item 3"]

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
    card["content"]["SERIES"] = series_display if series_display else _get_series_display_name(series_dir)
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
    card["content"]["OT_VERSE_LINE"] = f'{ot_ref} — "{ot_snip}"'
    card["content"]["NT_VERSE_LINE"] = f'{nt_ref} — "{nt_snip}"'

    card["content"]["GREEK"] = str(greek.get("text", "")).strip()
    card["content"]["GREEK_TRANSLIT"] = str(greek.get("translit", "")).strip()
    card["content"]["HEBREW"] = str(hebrew.get("text", "")).strip()
    card["content"]["HEBREW_TRANSLIT"] = str(hebrew.get("translit", "")).strip()
    card["content"]["OT_REFS"] = str(recipe.get("ot_refs", "")).strip()
    card["content"]["NT_REFS"] = str(recipe.get("nt_refs", "")).strip()
    card["content"]["TRIVIA_BULLETS"] = trivia_items

    card["grounding"] = grounding

    write_json(card_dir / "card.json", card)

    prompt_text = build_prompt_text(card)
    with open(card_dir / "prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt_text)

    _seed_revise_file(card_dir)

    # Use provided set_name (defaults to "Demo")
    demo_series = series_dir.name if series_dir else "2026-Q1"
    demo_set = set_name

    meta = {
        "number": f"{number:03d}",
        "word": word,
        "gloss": gloss,
        "card_type": card_type,
        "rarity": rarity,
        "series": demo_series,
        "set": demo_set,
        "art_prompt": art_prompt,
        "stats": {
            "lore": card["content"]["STAT_LORE"],
            "context": card["content"]["STAT_CONTEXT"],
            "complexity": card["content"]["STAT_COMPLEXITY"],
        },
        "ability": ability_text,
    }
    with open(card_dir / "meta.yml", "w", encoding="utf-8") as f:
        yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True)

    out_png = card_dir / "outputs" / "card_1024x1536.png"
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

    _log(f"[demo plan] completed: #{number:03d} {word}")
    return card_dir


def _plan_demo_card(
    *,
    series_dir: Path,
    template_path: Path,
    demo_dir: Path,
    entry: dict | None = None,
) -> Path | None:
    """Plan a single demo card (text gen + file creation). Returns card_dir or None on failure.

    If entry is provided, uses that word/type/rarity. Otherwise picks randomly.
    """
    if yaml is None:
        raise RuntimeError("pyyaml is required. Install with: pip install pyyaml")

    cards_dir = demo_dir
    number = next_number(cards_dir)

    if entry is None:
        entry = _pick_demo_entry(demo_dir)
    word = str(entry["word"]).upper()
    slug = slugify(word)
    card_type = str(entry.get("card_type", "NOUN")).strip().upper()
    rarity = str(entry.get("rarity", "COMMON")).strip().upper()

    _log(f"[demo plan] selected: #{number:03d} word={word} type={card_type} rarity={rarity}")

    card_dir = cards_dir / f"{number:03d}-{slug}"
    os.makedirs(card_dir, exist_ok=True)

    if not template_path.exists():
        print(f"Missing {template_path}")
        return None

    _log("[demo plan] generating recipe")
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
    card["content"]["SERIES"] = series_display if series_display else _get_series_display_name(series_dir)
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
    card["content"]["OT_VERSE_LINE"] = f'{ot_ref} — "{ot_snip}"'
    card["content"]["NT_VERSE_LINE"] = f'{nt_ref} — "{nt_snip}"'

    card["content"]["GREEK"] = str(greek.get("text", "")).strip()
    card["content"]["GREEK_TRANSLIT"] = str(greek.get("translit", "")).strip()
    card["content"]["HEBREW"] = str(hebrew.get("text", "")).strip()
    card["content"]["HEBREW_TRANSLIT"] = str(hebrew.get("translit", "")).strip()
    card["content"]["OT_REFS"] = str(recipe.get("ot_refs", "")).strip()
    card["content"]["NT_REFS"] = str(recipe.get("nt_refs", "")).strip()
    card["content"]["TRIVIA_BULLETS"] = trivia_items

    card["grounding"] = grounding

    write_json(card_dir / "card.json", card)
    _log(f"[demo plan] wrote card.json")

    prompt_text = build_prompt_text(card)
    with open(card_dir / "prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt_text)
    _log(f"[demo plan] wrote prompt.txt")

    _seed_revise_file(card_dir)
    _log(f"[demo plan] wrote revise.txt")

    # For demo cards, use "Demo" as the set name
    # Use style series for the series identifier, or fall back to current year-quarter
    demo_series = series_dir.name if series_dir else "2026-Q1"
    demo_set = "Demo"

    meta = {
        "number": f"{number:03d}",
        "word": word,
        "gloss": gloss,
        "card_type": card_type,
        "rarity": rarity,
        "series": demo_series,
        "set": demo_set,
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
    _log(f"[demo plan] wrote meta.yml")

    # Write post.md
    out_png = card_dir / "outputs" / "card_1024x1536.png"
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

    return card_dir


def phase_demo(*, style_series_dir: Path, template_path: Path, demo_dir: Path) -> int:
    """Generate a single demo card (plan + image)."""
    _log(f"[phase demo] demo_dir={demo_dir}")
    _log(f"[phase demo] template_path={template_path}")
    _log(f"[phase demo] style_series_dir={style_series_dir}")

    card_dir = _plan_demo_card(series_dir=style_series_dir, template_path=template_path, demo_dir=demo_dir)
    if card_dir is None:
        return 1

    # Generate image (no watermark for demo cards)
    rc = _generate_image_for_card_dir(
        card_dir=card_dir,
        skip_polish=False,
        skip_watermark=True,  # Demo cards don't need watermarks
        style_series_dir=style_series_dir,  # Use main series for style references
    )
    if rc != 0:
        return rc

    print(f"Generated demo card at {card_dir}")
    return 0


def phase_demo_batch(
    *,
    style_series_dir: Path,
    template_path: Path,
    demo_dir: Path,
    batch: int,
    parallel: int = 1,
    skip_polish: bool = False,
    skip_review: bool = False,
) -> int:
    """Generate multiple demo cards with pipelined parallel execution.

    Uses demo_dir for output and stats tracking, while using style_series_dir
    for style references (typically series/2026-Q1 with existing cards).

    Pipeline flow (cards flow through stages concurrently):
    1. Plan card recipe (text generation)
    2. Generate card image (style-referenced)
    3. Review and grade card (unless skip_review=True)

    Cards don't wait for all planning to complete before image generation starts.
    """
    demo_dir.mkdir(parents=True, exist_ok=True)
    out_name = "card_1024x1536.png"

    # -------------------------------------------------------------------------
    # PHASE 0: Image-first - Generate images for existing recipes missing images
    # -------------------------------------------------------------------------
    cards_needing_images: list[Path] = []
    for entry in sorted(demo_dir.iterdir()):
        if not entry.is_dir():
            continue
        prompt_file = entry / "prompt.txt"
        out_png = entry / "outputs" / out_name
        if prompt_file.exists() and not out_png.exists():
            cards_needing_images.append(entry)

    if cards_needing_images:
        _log(f"[demo batch] found {len(cards_needing_images)} existing recipes without images, generating first...")

        def generate_one(card_dir: Path) -> tuple[Path, int]:
            rc = _generate_image_for_card_dir(
                card_dir=card_dir,
                skip_polish=skip_polish,
                skip_watermark=True,
                style_series_dir=style_series_dir,
            )
            return card_dir, rc

        failed_existing: list[Path] = []
        completed = 0

        if parallel <= 1:
            for card_dir in cards_needing_images:
                card_dir, rc = generate_one(card_dir)
                completed += 1
                if rc != 0:
                    failed_existing.append(card_dir)
                _log(f"[demo batch] image-first: {completed}/{len(cards_needing_images)} ({card_dir.name})")
        else:
            with ThreadPoolExecutor(max_workers=parallel) as executor:
                futures = {executor.submit(generate_one, cd): cd for cd in cards_needing_images}
                for future in as_completed(futures):
                    card_dir, rc = future.result()
                    completed += 1
                    if rc != 0:
                        failed_existing.append(card_dir)
                    _log(f"[demo batch] image-first: {completed}/{len(cards_needing_images)} ({card_dir.name})")

        if failed_existing:
            _log(f"[demo batch] {len(failed_existing)} existing cards failed image generation:")
            for cd in failed_existing:
                _log(f"  - {cd.name}")

        _log(f"[demo batch] image-first phase complete: {completed - len(failed_existing)}/{len(cards_needing_images)} succeeded")

    # -------------------------------------------------------------------------
    # PHASE 1: Count existing cards, determine how many new cards to plan
    # -------------------------------------------------------------------------
    demo_stats = _load_series_stats(demo_dir)
    existing_total = demo_stats.get("total", 0)
    cards_to_plan = max(0, batch - existing_total)

    if cards_to_plan == 0:
        _log(f"[demo batch] already have {existing_total} cards, batch target {batch} reached")
        return 0

    _log(f"[demo batch] have {existing_total} cards, planning {cards_to_plan} more to reach {batch}...")

    # -------------------------------------------------------------------------
    # PHASE 2: Pre-generate word/type/rarity queue (single API call)
    # -------------------------------------------------------------------------
    series_words = _get_existing_words_from_index(style_series_dir)
    demo_words = _get_existing_words_from_index(demo_dir)
    existing_words = list(set(series_words + demo_words))
    _log(f"[demo batch] found {len(series_words)} series words + {len(demo_words)} demo words = {len(existing_words)} total to avoid")

    # Calculate needed rarities/types based on current stats
    planning_stats = dict(demo_stats)  # Copy for planning
    needed_rarities = []
    needed_types = []
    for _ in range(cards_to_plan):
        nr = _get_needed_rarity(planning_stats)
        nt = _get_needed_type(planning_stats)
        needed_rarities.append(nr)
        needed_types.append(nt)
        planning_stats["rarity_counts"][nr] = planning_stats["rarity_counts"].get(nr, 0) + 1
        planning_stats["type_counts"][nt] = planning_stats["type_counts"].get(nt, 0) + 1
        planning_stats["total"] += 1

    _log(f"[demo batch] planned rarities: {needed_rarities}")
    _log(f"[demo batch] planned types: {needed_types}")

    try:
        queue_entries = _generate_queue_entries(
            count=cards_to_plan,
            existing_words=existing_words,
            needed_rarities=needed_rarities,
            needed_types=needed_types,
            series_dir=style_series_dir,
        )
    except Exception as e:
        _log(f"[demo batch] failed to generate queue: {e}")
        return 1

    # Log actual distribution
    type_counts: dict[str, int] = {}
    rarity_counts: dict[str, int] = {}
    for entry in queue_entries:
        t = entry.get("card_type", "NOUN")
        r = entry.get("rarity", "COMMON")
        type_counts[t] = type_counts.get(t, 0) + 1
        rarity_counts[r] = rarity_counts.get(r, 0) + 1
    _log(f"[demo batch] actual types: {type_counts}")
    _log(f"[demo batch] actual rarities: {rarity_counts}")

    # -------------------------------------------------------------------------
    # PHASE 3: Pipeline - plan → generate → review per card (concurrent)
    # -------------------------------------------------------------------------
    start_number = next_number(demo_dir)
    _log(f"[demo batch] pre-allocating numbers {start_number} to {start_number + cards_to_plan - 1}")

    # Assign numbers to entries
    numbered_entries = [
        (start_number + i, entry) for i, entry in enumerate(queue_entries)
    ]

    # Results tracking (thread-safe)
    results_lock = threading.Lock()
    successful_cards: list[Path] = []
    failed_cards: list[Path] = []
    review_scores: list[int] = []
    stats_updates: list[dict] = []

    def process_card(number: int, entry: dict) -> None:
        """Full pipeline for one card: plan → generate → review."""
        word = entry['word']
        card_type = entry['card_type']
        rarity = entry['rarity']

        # STEP 1: Plan
        _log(f"[pipeline] #{number:03d} planning: {word} ({card_type}, {rarity})")
        card_dir = _plan_demo_card_with_number(
            series_dir=style_series_dir,
            template_path=template_path,
            demo_dir=demo_dir,
            number=number,
            entry=entry,
        )

        if card_dir is None:
            _log(f"[pipeline] #{number:03d} planning FAILED")
            with results_lock:
                failed_cards.append(None)  # Track failure
            return

        # Update index
        meta_file = card_dir / "meta.yml"
        ability_text = ""
        if meta_file.exists() and yaml:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = yaml.safe_load(f) or {}
            ability_text = meta.get("ability", "")

        with results_lock:
            _add_card_to_index(
                demo_dir,
                number=number,
                word=word,
                card_type=card_type,
                rarity=rarity,
                ability_text=ability_text,
            )
            stats_updates.append(entry)

        # STEP 2: Generate image
        _log(f"[pipeline] #{number:03d} generating image: {word}")
        rc = _generate_image_for_card_dir(
            card_dir=card_dir,
            skip_polish=skip_polish,
            skip_watermark=True,
            style_series_dir=style_series_dir,
        )

        if rc != 0:
            _log(f"[pipeline] #{number:03d} image generation FAILED")
            with results_lock:
                failed_cards.append(card_dir)
            return

        # STEP 3: Review (unless skipped)
        score = 0
        if not skip_review:
            _log(f"[pipeline] #{number:03d} reviewing: {word}")
            try:
                phase_review(card_dir=card_dir, max_attempts=2)
                # Read score from meta.yml
                if meta_file.exists() and yaml:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = yaml.safe_load(f) or {}
                    score = meta.get("review_score", 0)
                _log(f"[pipeline] #{number:03d} review complete: score={score}")
            except Exception as e:
                _log(f"[pipeline] #{number:03d} review failed: {e}")

        with results_lock:
            successful_cards.append(card_dir)
            if not skip_review:
                review_scores.append(score)

        _log(f"[pipeline] #{number:03d} COMPLETE: {word} (score={score})")

    _log(f"[demo batch] starting pipeline with {parallel} workers...")

    if parallel <= 1:
        for number, entry in numbered_entries:
            process_card(number, entry)
    else:
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = [
                executor.submit(process_card, num, ent)
                for num, ent in numbered_entries
            ]
            # Wait for all to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    _log(f"[pipeline] worker exception: {e}")

    # Update stats with actual completed counts
    if stats_updates:
        actual_stats = _load_series_stats(demo_dir)
        for entry in stats_updates:
            actual_stats["rarity_counts"][entry["rarity"]] = actual_stats["rarity_counts"].get(entry["rarity"], 0) + 1
            actual_stats["type_counts"][entry["card_type"]] = actual_stats["type_counts"].get(entry["card_type"], 0) + 1
            actual_stats["total"] += 1
        _save_series_stats(demo_dir, actual_stats)
        _log(f"[demo batch] updated stats.yml: total={actual_stats['total']}")

    # Summary
    if review_scores:
        avg_score = sum(review_scores) / len(review_scores)
        passing = len([s for s in review_scores if s >= 90])
        _log(f"[demo batch] review summary: avg={avg_score:.1f}, passing={passing}/{len(review_scores)}")

    total_success = len(successful_cards)
    total_failed = len(failed_cards)
    _log(f"[demo batch] complete: {total_success} succeeded, {total_failed} failed")

    # Final pass: check grade.json for actual pass/fail status
    _log(f"[demo batch] checking grade results...")
    graded_passed = 0
    graded_failed = 0
    failed_card_names = []

    for card_dir in sorted(demo_dir.iterdir()):
        if not card_dir.is_dir():
            continue
        if not card_dir.name[0].isdigit():
            continue

        grade_path = card_dir / "grade.json"
        if grade_path.exists():
            grade = read_json(grade_path)
            if grade.get("passed", False):
                graded_passed += 1
            else:
                graded_failed += 1
                failed_card_names.append(card_dir.name)

    _log(f"[demo batch] grade results: {graded_passed} passed, {graded_failed} failed")
    if failed_card_names:
        _log(f"[demo batch] failed cards: {', '.join(failed_card_names[:10])}{'...' if len(failed_card_names) > 10 else ''}")

        # Ask if user wants to run rebuild-failed
        try:
            response = input(f"\n{graded_failed} cards failed grading. Run rebuild-failed now? [y/N]: ").strip().lower()
            if response == 'y':
                _log(f"[demo batch] running rebuild-failed phase...")
                phase_rebuild_failed(cards_dir=demo_dir, parallel=1)
        except (EOFError, KeyboardInterrupt):
            _log(f"[demo batch] skipping rebuild-failed")

    return 0 if total_failed == 0 else 1


def phase_example_cards(
    *,
    style_series_dir: Path,
    template_path: Path,
    example_dir: Path,
    parallel: int = 1,
    skip_polish: bool = False,
    target_type: str | None = None,
    target_rarity: str | None = None,
    ask_before_review: bool = False,
    count: int = 0,
    override_style_refs: list[str] | None = None,
) -> int:
    """Generate example cards from queue.yml in example_dir.

    Reads cards from templates/example_cards/queue.yml and generates them one by one.
    If target_type and/or target_rarity are specified, only generates matching cards.
    If override_style_refs is provided, uses only those refs instead of programmatic ones.
    """
    example_dir.mkdir(parents=True, exist_ok=True)
    queue_path = example_dir / "queue.yml"

    if not queue_path.exists():
        print(f"Queue file not found: {queue_path}")
        print("Create a queue.yml with entries like:")
        print("  - word: GRACE")
        print("    card_type: NOUN")
        print("    rarity: COMMON")
        return 2

    # Load queue
    queue = load_queue(queue_path)
    if not queue:
        print("Queue is empty.")
        return 0

    _log(f"[example cards] loaded {len(queue)} entries from queue")
    _log(f"[example cards] output: {example_dir}")
    _log(f"[example cards] style_series: {style_series_dir}")

    # Filter by target if specified
    types = ["NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE"]
    rarities = ["COMMON", "UNCOMMON", "RARE", "GLORIOUS"]

    if target_type:
        target_type = target_type.upper()
        if target_type not in types:
            print(f"Invalid type: {target_type}. Valid types: {', '.join(types)}")
            return 2

    if target_rarity:
        target_rarity = target_rarity.upper()
        if target_rarity not in rarities:
            print(f"Invalid rarity: {target_rarity}. Valid rarities: {', '.join(rarities)}")
            return 2

    # Build entries with card numbers (position in queue)
    entries: list[dict] = []
    skipped_complete = 0
    for i, q in enumerate(queue):
        card_type = str(q.get("card_type", "NOUN")).upper()
        rarity = str(q.get("rarity", "COMMON")).upper()
        word = str(q.get("word", "EXAMPLE")).upper()
        num = i + 1

        # Filter if targets specified
        if target_type and card_type != target_type:
            continue
        if target_rarity and rarity != target_rarity:
            continue

        # Skip cards that already have completed output
        card_dir = example_dir / f"{num:03d}-{word.lower()}"
        card_png = card_dir / "outputs" / "card_1024x1536.png"
        if card_png.exists():
            skipped_complete += 1
            continue

        entries.append({
            "number": num,
            "word": word,
            "card_type": card_type,
            "rarity": rarity,
        })

    if not entries:
        if skipped_complete > 0:
            print(f"All cards complete! ({skipped_complete} already generated)")
        else:
            print("No matching cards in queue after filtering.")
        return 0

    if skipped_complete > 0:
        _log(f"[example cards] skipped {skipped_complete} already-completed cards")

    # Limit entries if count specified
    if count > 0 and len(entries) > count:
        _log(f"[example cards] limiting to {count} card(s) (--count)")
        entries = entries[:count]

    _log(f"[example cards] generating {len(entries)} cards:")
    for e in entries:
        _log(f"  #{e['number']:03d} {e['word']} ({e['card_type']}, {e['rarity']})")

    # Results tracking
    results_lock = threading.Lock()
    successful: list[Path] = []
    failed: list[Path] = []

    def process_card(entry: dict) -> None:
        num = entry["number"]
        word = entry["word"]
        card_type = entry["card_type"]
        rarity = entry["rarity"]

        _log(f"[example] #{num:03d} planning: {word} ({card_type}, {rarity})")

        card_dir = _plan_demo_card_with_number(
            series_dir=style_series_dir,
            template_path=template_path,
            demo_dir=example_dir,
            number=num,
            entry=entry,
            set_name="Example",
            series_display="Example",
        )

        if card_dir is None:
            _log(f"[example] #{num:03d} planning FAILED")
            with results_lock:
                failed.append(None)
            return

        _log(f"[example] #{num:03d} generating image: {word}")
        rc = _generate_image_for_card_dir(
            card_dir=card_dir,
            skip_polish=skip_polish,
            skip_watermark=True,
            style_series_dir=style_series_dir,
            templates_only=True if not override_style_refs else False,
            override_style_refs=override_style_refs,
        )

        if rc != 0:
            _log(f"[example] #{num:03d} image generation FAILED")
            with results_lock:
                failed.append(card_dir)
            return

        # Run review/grading (with optional confirmation)
        run_review = True
        if ask_before_review:
            out_png = card_dir / "outputs" / "card_1024x1536.png"
            print(f"\n{'='*60}")
            print(f"Image generated: {out_png}")
            print(f"{'='*60}")
            response = input("Continue to review phase? [Y/n/skip]: ").strip().lower()
            if response in ("n", "no", "skip"):
                run_review = False
                _log(f"[example] #{num:03d} review SKIPPED by user")

        if run_review:
            _log(f"[example] #{num:03d} reviewing: {word}")
            try:
                phase_review(card_dir=card_dir, max_attempts=2)
            except Exception as e:
                _log(f"[example] #{num:03d} review failed: {e}")

        with results_lock:
            successful.append(card_dir)
        _log(f"[example] #{num:03d} COMPLETE: {word}")

    _log(f"[example cards] starting with {parallel} workers...")

    if parallel <= 1:
        for entry in entries:
            process_card(entry)
    else:
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = [executor.submit(process_card, e) for e in entries]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    _log(f"[example] worker exception: {e}")

    _log(f"[example cards] complete: {len(successful)} succeeded, {len(failed)} failed")

    # Update stats
    stats = {
        "total": len(successful),
        "type_counts": {},
        "rarity_counts": {},
    }
    for entry in entries:
        t = entry["card_type"]
        r = entry["rarity"]
        stats["type_counts"][t] = stats["type_counts"].get(t, 0) + 1
        stats["rarity_counts"][r] = stats["rarity_counts"].get(r, 0) + 1
    _save_series_stats(example_dir, stats)

    return 0 if len(failed) == 0 else 1


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

    # Get target rarity and type from meta.yml
    target_rarity = None
    target_type = None
    meta_file = target_dir / "meta.yml"
    if meta_file.exists() and yaml:
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}
        target_rarity = meta.get("rarity", "").upper() or None
        target_type = (meta.get("card_type") or meta.get("type", "")).upper() or None

    _log(f"[phase imagegen] generating image for {target_dir.name} -> {out_png} (rarity={target_rarity}, type={target_type})")

    style_refs, rarity_labels, fix_mode = _build_style_refs(
        series_dir,
        target_rarity=target_rarity,
        target_type=target_type,
        fix_mode=False,
    )
    if style_refs:
        cmd = [
            sys.executable, "-m", "hypertext.gemini.style",
            "--prompt-file", str(prompt_file),
            *_build_style_cmd_args(style_refs, rarity_labels, target_rarity, fix_mode),
            "--out", str(out_png)
        ]
    else:
        cmd = [
            sys.executable, "-m", "hypertext.gemini.image",
            str(prompt_file),
            str(out_png)
        ]
        
    subprocess.check_call(cmd)

    # Skip polish here - review phase will run polish after evaluation
    # This avoids running polish twice in the daily flow: imagegen → review → polish
    _log("[phase imagegen] skipping polish (will run after review)")

    _run_watermark(card_dir=target_dir, image_path=out_png)

    print(f"Rendered image at {out_png}")
    return 0


def _generate_image_for_card_dir(
    *,
    card_dir: Path,
    skip_polish: bool = False,
    skip_watermark: bool = False,
    style_series_dir: Path | None = None,
    templates_only: bool = False,
    override_style_refs: list[str] | None = None,
) -> int:
    out_name = "card_1024x1536.png"
    prompt_file = card_dir / "prompt.txt"
    if not prompt_file.exists():
        print(f"Missing {prompt_file}")
        return 1

    out_png = card_dir / "outputs" / out_name
    out_png.parent.mkdir(parents=True, exist_ok=True)

    # Get target rarity, type, and style_series from meta.yml
    target_rarity = None
    target_type = None
    stored_style_series = None
    meta_file = card_dir / "meta.yml"
    meta = {}
    if meta_file.exists() and yaml:
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}
        target_rarity = meta.get("rarity", "").upper() or None
        target_type = (meta.get("card_type") or meta.get("type", "")).upper() or None
        stored_style_series = meta.get("style_series_dir")

    _log(f"[batch] generating image for {card_dir.name} -> {out_png} (rarity={target_rarity}, type={target_type})")

    # Use provided style_series_dir, stored value from meta, or infer from card_dir
    if style_series_dir:
        series_dir = style_series_dir
        # Store for future rebuilds (e.g., review phase)
        if yaml and str(style_series_dir) != stored_style_series:
            meta["style_series_dir"] = str(style_series_dir)
            with open(meta_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True)
    elif stored_style_series:
        series_dir = Path(stored_style_series)
    else:
        series_dir = card_dir.parent.parent
    if override_style_refs:
        style_refs = list(override_style_refs)
        rarity_labels = {}
        fix_mode = False
        _log(f"[batch] Using {len(style_refs)} override style refs")
    else:
        style_refs, rarity_labels, fix_mode = _build_style_refs(
            series_dir,
            target_rarity=target_rarity,
            target_type=target_type,
            fix_mode=False,
            templates_only=templates_only,
        )
    if style_refs:
        cmd = [
            sys.executable, "-m", "hypertext.gemini.style",
            "--prompt-file", str(prompt_file),
            *_build_style_cmd_args(style_refs, rarity_labels, target_rarity, fix_mode),
            "--out", str(out_png)
        ]
    else:
        cmd = [
            sys.executable, "-m", "hypertext.gemini.image",
            str(prompt_file),
            str(out_png)
        ]

    subprocess.check_call(cmd)

    # Run polish step (optional)
    if not skip_polish:
        polish_cmd = [
            sys.executable, "-m", "hypertext.cards.polish",
            str(out_png)
        ]
        try:
            subprocess.check_call(polish_cmd)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Polish step failed: {e}")
    else:
        _log(f"[batch] skipping polish step")

    # Run watermark step (optional)
    if not skip_watermark:
        _run_watermark(card_dir=card_dir, image_path=out_png)
    else:
        _log(f"[batch] skipping watermark step")

    print(f"Rendered image at {out_png}")
    return 0


def phase_batch(
    *,
    series_dir: Path,
    template_path: Path,
    auto: bool,
    batch: int,
    parallel: int = 1,
    skip_polish: bool = False,
    skip_watermark: bool = False,
) -> int:
    cards_dir = series_dir / "cards"
    planned_cards: list[Path] = []

    # Phase 1: Plan all cards sequentially (need unique card numbers)
    _log(f"[batch] planning {batch} cards...")
    for i in range(batch):
        _log(f"[batch] planning card {i + 1}/{batch}")
        before = find_latest_card_dir(cards_dir)
        rc = phase_plan(series_dir=series_dir, template_path=template_path, auto=auto)
        if rc != 0:
            _log(f"[batch] planning failed at card {i + 1}")
            break
        after = find_latest_card_dir(cards_dir)
        if after is None or after == before:
            _log("[batch] no new card planned; stopping")
            break
        planned_cards.append(after)

    if not planned_cards:
        _log("[batch] no cards were planned")
        return 0

    _log(f"[batch] planned {len(planned_cards)} cards, generating images with {parallel} parallel workers...")

    # Phase 2: Generate images in parallel
    failed_cards: list[Path] = []
    completed_count = 0

    def generate_one(card_dir: Path) -> tuple[Path, int]:
        rc = _generate_image_for_card_dir(
            card_dir=card_dir,
            skip_polish=skip_polish,
            skip_watermark=skip_watermark,
        )
        return card_dir, rc

    if parallel <= 1:
        # Sequential execution
        for card_dir in planned_cards:
            card_dir, rc = generate_one(card_dir)
            completed_count += 1
            if rc != 0:
                failed_cards.append(card_dir)
            _log(f"[batch] completed {completed_count}/{len(planned_cards)}")
    else:
        # Parallel execution
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {executor.submit(generate_one, cd): cd for cd in planned_cards}
            for future in as_completed(futures):
                card_dir, rc = future.result()
                completed_count += 1
                if rc != 0:
                    failed_cards.append(card_dir)
                _log(f"[batch] completed {completed_count}/{len(planned_cards)} ({card_dir.name})")

    if failed_cards:
        _log(f"[batch] {len(failed_cards)} cards failed image generation:")
        for cd in failed_cards:
            _log(f"  - {cd.name}")
        return 1

    _log(f"[batch] all {len(planned_cards)} cards completed successfully")
    return 0


def phase_revise(*, card_dir: Path, revise_file: Path | None, override_style_refs: list[str] | None = None, extra_style_refs: list[str] | None = None, inline_revision: str | None = None, image_only: bool = False) -> int:
    if yaml is None:
        raise RuntimeError("pyyaml is required. Install with: pip install pyyaml")

    _log(f"[phase revise] card_dir={card_dir}")

    card_path = card_dir / "card.json"
    if not card_path.exists():
        print(f"Missing {card_path}")
        return 1

    card = read_json(card_path)

    # Handle image-only mode (skip JSON patching, just regenerate with revision in prompt)
    if image_only and inline_revision:
        _log(f"[phase revise] Image-only mode with revision: {inline_revision[:50]}...")
        out_png = card_dir / "outputs" / "card_1024x1536.png"
        prompt_path = card_dir / "prompt.txt"

        # Read existing prompt and append revision
        existing_prompt = _read_text(prompt_path) if prompt_path.exists() else ""
        revised_prompt = existing_prompt + f"\n\nREVISION INSTRUCTIONS:\n{inline_revision}"
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(revised_prompt)
        _log(f"[phase revise] Updated prompt with revision instructions")

        target_rarity = card.get("content", {}).get("RARITY_TEXT", "").upper() or None
        target_type = card.get("content", {}).get("CARD_TYPE", "").upper() or None

        series_dir = card_dir.parent.parent
        is_example_card = "example_cards" in str(card_dir)
        if is_example_card:
            _log("[phase revise] Example card detected - using templates only for style refs")

        # Build style refs
        if override_style_refs:
            style_refs = list(override_style_refs)
            rarity_labels = {}
        else:
            style_refs, rarity_labels, _ = _build_style_refs(
                series_dir,
                current_card_path=out_png if out_png.exists() else None,
                target_rarity=target_rarity,
                target_type=target_type,
                fix_mode=out_png.exists(),
                templates_only=is_example_card,
            )
            if extra_style_refs:
                extra_resolved = [str(Path(r).resolve()) for r in extra_style_refs]
                existing_resolved = [str(Path(r).resolve()) for r in style_refs]
                new_extras = [r for r, res in zip(extra_style_refs, extra_resolved) if res not in existing_resolved]
                if new_extras:
                    if out_png.exists() and style_refs:
                        style_refs = [style_refs[0]] + new_extras + style_refs[1:]
                    else:
                        style_refs = new_extras + style_refs
                    _log(f"[phase revise] Added {len(new_extras)} extra style refs")

        use_fix_mode = out_png.exists()
        if style_refs:
            cmd = [
                sys.executable, "-m", "hypertext.gemini.style",
                "--prompt-file", str(prompt_path),
                *_build_style_cmd_args(style_refs, rarity_labels, target_rarity, use_fix_mode),
                "--out", str(out_png)
            ]
        else:
            cmd = [
                sys.executable, "-m", "hypertext.gemini.image",
                str(prompt_path),
                str(out_png)
            ]

        subprocess.check_call(cmd)
        _log("[phase revise] image-only revision complete")
        _run_watermark(card_dir=card_dir, image_path=out_png)
        print(f"Revised card (image-only) at {card_dir}")
        return 0

    # Handle inline revision (--revision flag) or file-based revision
    if inline_revision:
        _log(f"[phase revise] Using inline revision: {inline_revision[:50]}...")
        # Create a minimal form result with just the instructions
        from dataclasses import dataclass
        @dataclass
        class InlineFormResult:
            instructions: str
            rebuild: bool = False
            allowed_paths: list = None
        form_result = InlineFormResult(instructions=f"General_Revision_Request:\n{inline_revision}", allowed_paths=[])
    else:
        revise_path = revise_file if revise_file is not None else (card_dir / "revise.txt")
        if not revise_path.exists():
            print(f"Missing {revise_path}. Add your edit instructions there and rerun revise.")
            return 1
        raw_instructions = _read_text(revise_path)
        form_result = _parse_revise_form(raw_instructions, card=card)

    # Handle rebuild-only case (no content changes, just regenerate image)
    if form_result.rebuild and not form_result.instructions:
        _log("[phase revise] Rebuild requested with no content changes")
        # Just regenerate the image from scratch
        out_png = card_dir / "outputs" / "card_1024x1536.png"
        target_rarity = card.get("content", {}).get("RARITY_TEXT", "").upper() or None
        target_type = card.get("content", {}).get("CARD_TYPE", "").upper() or None

        _log(f"[phase revise] rebuilding image -> {out_png} (rarity={target_rarity}, type={target_type})")

        series_dir = card_dir.parent.parent
        # Detect if this is an example card (use templates only for style refs)
        is_example_card = "example_cards" in str(card_dir)
        if is_example_card:
            _log("[phase revise] Example card detected - using templates only for style refs")

        # Rebuild does NOT use fix_mode - generating fresh from scratch
        if override_style_refs:
            # Complete override - use only the provided refs
            style_refs = list(override_style_refs)
            rarity_labels = {}
            _log(f"[phase revise] Using {len(style_refs)} override style refs (replacing programmatic refs)")
        else:
            style_refs, rarity_labels, _ = _build_style_refs(
                series_dir,
                target_rarity=target_rarity,
                target_type=target_type,
                fix_mode=False,
                templates_only=is_example_card,
            )
            # Add extra style refs at start (highest priority), deduped
            if extra_style_refs:
                extra_resolved = [str(Path(r).resolve()) for r in extra_style_refs]
                existing_resolved = [str(Path(r).resolve()) for r in style_refs]
                new_extras = [r for r, res in zip(extra_style_refs, extra_resolved) if res not in existing_resolved]
                if new_extras:
                    style_refs = new_extras + style_refs
                    _log(f"[phase revise] Added {len(new_extras)} extra style refs (highest priority)")
        if style_refs:
            cmd = [
                sys.executable, "-m", "hypertext.gemini.style",
                "--prompt-file", str(card_dir / "prompt.txt"),
                *_build_style_cmd_args(style_refs, rarity_labels, target_rarity, False),
                "--out", str(out_png)
            ]
        else:
            cmd = [
                sys.executable, "-m", "hypertext.gemini.image",
                str(card_dir / "prompt.txt"),
                str(out_png)
            ]

        subprocess.check_call(cmd)
        _log("[phase revise] image rebuild complete")

        _run_watermark(card_dir=card_dir, image_path=out_png)

        # Update meta with rebuild note
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
            meta["revision_notes"] = "Rebuild (image regenerated from scratch)"
            with open(meta_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True)

        # Write changes file for PR comment
        changes_path = card_dir / ".revision_changes.txt"
        changes_path.write_text("Rebuild: image regenerated from scratch\n", encoding="utf-8")

        # Reset revise.txt with Rebuild: false so user can trigger new rebuilds
        _seed_revise_file(card_dir, force=True)

        print(f"Rebuilt card at {card_dir}")
        return 0

    # Normal revision flow (with or without rebuild)
    if not form_result.instructions:
        print(
            f"No revision instructions found in {revise_path}. "
            "Edit revise.txt (add non-comment text) or set Rebuild: true and rerun revise."
        )
        return 1

    instructions = form_result.instructions
    allowed_paths = form_result.allowed_paths

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

    # Get target rarity and type from updated card
    target_rarity = updated.get("content", {}).get("RARITY_TEXT", "").upper() or None
    target_type = updated.get("content", {}).get("CARD_TYPE", "").upper() or None

    _log(f"[phase revise] generating image -> {out_png} (rarity={target_rarity}, type={target_type})")

    # Detect if this is an example card (use templates only for style refs)
    is_example_card = "example_cards" in str(card_dir)
    if is_example_card:
        _log("[phase revise] Example card detected - using templates only for style refs")

    # Get stored style_series_dir from meta.yml (set during initial generation)
    stored_style_series = None
    meta_path = card_dir / "meta.yml"
    if meta_path.exists() and yaml:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}
        stored_style_series = meta.get("style_series_dir")

    # Use stored style_series_dir if available, otherwise infer from card path
    if stored_style_series:
        series_dir = Path(stored_style_series)
        _log(f"[phase revise] using stored style_series_dir: {series_dir}")
    else:
        # For demo/example cards (no stored path), default to the main series with style refs
        if "demo_cards" in str(card_dir) or "example_cards" in str(card_dir) or not (card_dir.parent.parent / "cards").exists():
            series_dir = DEFAULT_SERIES_DIR
            _log(f"[phase revise] Demo/example card detected, using default series: {series_dir}")
        else:
            series_dir = card_dir.parent.parent

    # If rebuild flag is set, use fix_mode=False to generate fresh image
    # Otherwise, use fix_mode for incremental fixes
    use_fix_mode = not form_result.rebuild and out_png.exists()

    if form_result.rebuild:
        _log("[phase revise] Rebuild requested - generating fresh image")

    if override_style_refs:
        # Complete override - use only the provided refs
        style_refs = list(override_style_refs)
        rarity_labels = {}
        _log(f"[phase revise] Using {len(style_refs)} override style refs (replacing programmatic refs)")
    else:
        style_refs, rarity_labels, _ = _build_style_refs(
            series_dir,
            current_card_path=out_png if use_fix_mode else None,
            target_rarity=target_rarity,
            target_type=target_type,
            fix_mode=use_fix_mode,
            templates_only=is_example_card,
        )
        # Add extra style refs after current card (for fix_mode) or at start
        if extra_style_refs:
            # Dedupe - remove any extra refs that are already in the list
            extra_resolved = [str(Path(r).resolve()) for r in extra_style_refs]
            existing_resolved = [str(Path(r).resolve()) for r in style_refs]
            new_extras = [r for r, res in zip(extra_style_refs, extra_resolved) if res not in existing_resolved]
            if new_extras:
                if use_fix_mode and style_refs:
                    # Insert after current card [1], before templates
                    style_refs = [style_refs[0]] + new_extras + style_refs[1:]
                else:
                    style_refs = new_extras + style_refs
                _log(f"[phase revise] Added {len(new_extras)} extra style refs")
    if style_refs:
        cmd = [
            sys.executable, "-m", "hypertext.gemini.style",
            "--prompt-file", str(card_dir / "prompt.txt"),
            *_build_style_cmd_args(style_refs, rarity_labels, target_rarity, use_fix_mode),
            "--out", str(out_png)
        ]
    else:
        cmd = [
            sys.executable, "-m", "hypertext.gemini.image",
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

    # Build changes summary for PR comment
    changes_lines: list[str] = []
    if form_result.rebuild:
        changes_lines.append("**Mode:** Rebuild (fresh image generation)")
    else:
        changes_lines.append("**Mode:** Revise (incremental fix)")

    if form_result.card_changes:
        changes_lines.append("")
        changes_lines.append("**Field changes:**")
        for field, (old_val, new_val) in form_result.card_changes.items():
            # Truncate long values for readability
            old_display = old_val[:50] + "..." if len(old_val) > 50 else old_val
            new_display = new_val[:50] + "..." if len(new_val) > 50 else new_val
            changes_lines.append(f"- `{field}`: {old_display} → {new_display}")

    if instructions:
        changes_lines.append("")
        changes_lines.append("**Instructions:**")
        # Add first few lines of instructions
        instr_lines = instructions.split("\n")[:5]
        for line in instr_lines:
            if line.strip():
                changes_lines.append(f"> {line}")
        if len(instructions.split("\n")) > 5:
            changes_lines.append("> ...")

    # Write changes to file for workflow to read
    changes_path = card_dir / ".revision_changes.txt"
    changes_path.write_text("\n".join(changes_lines), encoding="utf-8")

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
        if form_result.rebuild:
            meta["last_rebuild"] = True
        with open(meta_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True)

    # Update revise.txt with new card data for next revision
    _seed_revise_file(card_dir, force=True)

    action = "Rebuilt" if form_result.rebuild else "Revised"
    print(f"{action} card at {card_dir}")
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

    # Get target rarity and type from card
    target_rarity = card.get("content", {}).get("RARITY_TEXT", "").upper() or None
    target_type = card.get("content", {}).get("TYPE", "").upper() or None

    _log(f"[phase rebuild] generating image -> {out_png} (rarity={target_rarity}, type={target_type})")

    # Get stored style_series_dir from meta.yml (set during initial generation)
    stored_style_series = None
    meta_path = card_dir / "meta.yml"
    if meta_path.exists() and yaml:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}
        stored_style_series = meta.get("style_series_dir")

    # Use stored style_series_dir if available, otherwise infer from card path
    if stored_style_series:
        series_dir = Path(stored_style_series)
        _log(f"[phase rebuild] using stored style_series_dir: {series_dir}")
    else:
        # For demo cards (no stored path), default to the main series with style refs
        if "demo_cards" in str(card_dir) or not (card_dir.parent.parent / "cards").exists():
            series_dir = DEFAULT_SERIES_DIR
            _log(f"[phase rebuild] Demo card detected, using default series: {series_dir}")
        else:
            series_dir = card_dir.parent.parent

    # Rebuild does NOT use fix_mode - generating fresh from scratch
    style_refs, rarity_labels, fix_mode = _build_style_refs(
        series_dir,
        target_rarity=target_rarity,
        target_type=target_type,
        fix_mode=False,
    )
    if style_refs:
        cmd = [
            sys.executable, "-m", "hypertext.gemini.style",
            "--prompt-file", str(prompt_path),
            *_build_style_cmd_args(style_refs, rarity_labels, target_rarity, fix_mode),
            "--out", str(out_png)
        ]
    else:
        cmd = [
            sys.executable, "-m", "hypertext.gemini.image",
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


def phase_rebuild_failed(*, cards_dir: Path, parallel: int = 1) -> int:
    """Find all failed cards and rebuild them.

    Scans cards_dir for cards with grade.json where passed=false,
    then rebuilds each one.

    Args:
        cards_dir: Directory containing card folders (e.g., demo_cards)
        parallel: Number of cards to rebuild in parallel

    Returns:
        Number of cards that still failed after rebuild
    """
    _log(f"[phase rebuild_failed] Scanning {cards_dir} for failed cards...")

    failed_cards = []

    for card_dir in sorted(cards_dir.iterdir()):
        if not card_dir.is_dir():
            continue
        if not card_dir.name[0].isdigit():
            continue

        grade_path = card_dir / "grade.json"
        if not grade_path.exists():
            continue

        grade = read_json(grade_path)
        if not grade.get("passed", True):
            failed_cards.append(card_dir)
            _log(f"  Found failed: {card_dir.name} (score: {grade.get('score', '?')})")

    if not failed_cards:
        print("No failed cards found!")
        return 0

    print(f"Found {len(failed_cards)} failed cards to rebuild:")
    for card_dir in failed_cards:
        print(f"  - {card_dir.name}")
    print()

    # Rebuild each failed card
    still_failed = 0
    for i, card_dir in enumerate(failed_cards):
        print(f"\n[{i+1}/{len(failed_cards)}] Rebuilding {card_dir.name}...")

        try:
            result = phase_rebuild(card_dir=card_dir, regen_prompt=False)
            if result != 0:
                still_failed += 1
                continue

            # Re-grade after rebuild
            _log(f"[phase rebuild_failed] Re-grading {card_dir.name}...")
            grade_result = phase_grade(card_dir=card_dir)

            # Check if it passed now
            grade_path = card_dir / "grade.json"
            if grade_path.exists():
                grade = read_json(grade_path)
                if grade.get("passed", False):
                    print(f"  {card_dir.name} now PASSED (score: {grade.get('score', '?')})")
                else:
                    print(f"  {card_dir.name} still FAILED (score: {grade.get('score', '?')})")
                    still_failed += 1
            else:
                still_failed += 1

        except Exception as e:
            print(f"  ERROR rebuilding {card_dir.name}: {e}")
            still_failed += 1

    print(f"\n=== Rebuild Complete ===")
    print(f"Rebuilt: {len(failed_cards)} cards")
    print(f"Still failed: {still_failed}")

    return still_failed


def _generate_image_only(*, card_dir: Path) -> Path:
    """Generate image without polish. Returns path to generated image."""
    out_name = "card_1024x1536.png"
    prompt_file = card_dir / "prompt.txt"
    if not prompt_file.exists():
        raise RuntimeError(f"Missing {prompt_file}")

    out_png = card_dir / "outputs" / out_name
    out_png.parent.mkdir(parents=True, exist_ok=True)

    # Get target rarity, type, and style_series from meta.yml
    target_rarity = None
    target_type = None
    stored_style_series = None
    meta_file = card_dir / "meta.yml"
    if meta_file.exists() and yaml:
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}
        target_rarity = meta.get("rarity", "").upper() or None
        target_type = (meta.get("card_type") or meta.get("type", "")).upper() or None
        stored_style_series = meta.get("style_series_dir")

    _log(f"[imagegen] generating image for {card_dir.name} -> {out_png} (rarity={target_rarity}, type={target_type})")

    # Use stored style_series_dir if available, otherwise infer from card path
    if stored_style_series:
        series_dir = Path(stored_style_series)
        _log(f"[imagegen] using stored style_series_dir: {series_dir}")
    else:
        # For demo cards (no stored path), default to the main series with style refs
        if "demo_cards" in str(card_dir) or not (card_dir.parent.parent / "cards").exists():
            series_dir = DEFAULT_SERIES_DIR
            _log(f"[imagegen] Demo card detected, using default series: {series_dir}")
        else:
            series_dir = card_dir.parent.parent

    # Check if this is an example card (use templates only, no series cards)
    is_example_card = "example_cards" in str(card_dir)
    if is_example_card:
        _log(f"[imagegen] Example card detected - using templates only")

    style_refs, rarity_labels, fix_mode = _build_style_refs(
        series_dir,
        target_rarity=target_rarity,
        target_type=target_type,
        fix_mode=False,
        templates_only=is_example_card,
    )
    if style_refs:
        cmd = [
            sys.executable, "-m", "hypertext.gemini.style",
            "--prompt-file", str(prompt_file),
            *_build_style_cmd_args(style_refs, rarity_labels, target_rarity, fix_mode),
            "--out", str(out_png)
        ]
    else:
        cmd = [
            sys.executable, "-m", "hypertext.gemini.image",
            str(prompt_file),
            str(out_png)
        ]

    subprocess.check_call(cmd)
    return out_png


def _run_polish(image_path: Path) -> None:
    """Run polish step to remove brackets."""
    polish_cmd = [
        sys.executable, "-m", "hypertext.cards.polish",
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
        sys.executable, "-m", "hypertext.watermark.crypto",
        "--card-dir",
        str(card_dir),
        "--out",
        str(watermark_svg),
    ]
    cmd_apply = [
        sys.executable, "-m", "hypertext.watermark.apply",
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


def phase_grade(*, card_dir: Path, style_series_dir: Path | None = None) -> int:
    """
    Grade-only phase for a card image (no rebuild, just assessment).

    Like lot grading - uses two-stage approach:
    1. First analyze style references to build a rubric
    2. Then grade the test card against both refs and rubric

    Returns 0 on success, 1 on error.
    """
    if yaml is None:
        raise RuntimeError("pyyaml is required. Install with: pip install pyyaml")

    _log(f"[phase grade] card_dir={card_dir}")

    card_path = card_dir / "card.json"
    if not card_path.exists():
        print(f"Missing {card_path}")
        return 1

    out_png = card_dir / "outputs" / "card_1024x1536.png"
    if not out_png.exists():
        print(f"Missing {out_png}. Run imagegen first.")
        return 1

    card_json = read_json(card_path)
    content = card_json.get("content", {})
    word = content.get("WORD", "UNKNOWN")
    target_rarity = content.get("RARITY", "COMMON")
    target_type = content.get("CARD_TYPE", "NOUN")

    _log(f"[phase grade] Grading {word} ({target_type}, {target_rarity})")

    # Determine style series directory
    if style_series_dir:
        series_dir = style_series_dir
        _log(f"[phase grade] Using explicit style_series_dir: {series_dir}")
    else:
        # Check meta.yml for stored style_series_dir
        stored_style_series = None
        meta_path = card_dir / "meta.yml"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = yaml.safe_load(f) or {}
            stored_style_series = meta.get("style_series_dir")

        if stored_style_series:
            series_dir = Path(stored_style_series)
            _log(f"[phase grade] Using stored style_series_dir: {series_dir}")
        else:
            # For demo cards, default to main series
            if "demo_cards" in str(card_dir) or not (card_dir.parent.parent / "cards").exists():
                series_dir = DEFAULT_SERIES_DIR
                _log(f"[phase grade] Demo card detected, using default series: {series_dir}")
            else:
                series_dir = card_dir.parent.parent
                _log(f"[phase grade] Using inferred series_dir: {series_dir}")

    # Build style references
    _log(f"[phase grade] Building style refs from {series_dir}...")
    style_refs, rarity_labels, _ = _build_style_refs(
        series_dir,
        target_rarity=target_rarity,
        target_type=target_type,
        fix_mode=False,
    )

    _log(f"[phase grade] Built {len(style_refs)} style reference(s):")
    for i, ref in enumerate(style_refs, 1):
        ref_path = Path(ref)
        label = rarity_labels.get(i, "")
        if "template" in ref.lower():
            _log(f"  [{i}] TEMPLATE: {ref_path.name}")
        else:
            _log(f"  [{i}] REFERENCE: {ref_path.name} {label}")

    if len(style_refs) < 2:
        _log("[phase grade] WARNING: Only 1 style reference - style matching may be unreliable!")
        _log("[phase grade] Expected: 1 template + 3 matching cards = 4 references")

    # Load static style rubric (pre-generated from reference analysis)
    _log("[phase grade] Loading style rubric...")
    style_rubric = None
    if DEFAULT_STYLE_RUBRIC.exists():
        with open(DEFAULT_STYLE_RUBRIC, "r", encoding="utf-8") as f:
            style_rubric = f.read()
        _log(f"[phase grade] Loaded style rubric ({len(style_rubric)} chars) from {DEFAULT_STYLE_RUBRIC.name}")
    else:
        _log(f"[phase grade] WARNING: Style rubric not found at {DEFAULT_STYLE_RUBRIC}")
        _log("[phase grade] Generating rubric dynamically (slower)...")
        try:
            style_rubric = describe_card_style_references(style_refs)
            _log(f"[phase grade] Style rubric generated ({len(style_rubric)} chars)")
        except Exception as e:
            _log(f"[phase grade] Style rubric generation failed: {e}")
            style_rubric = None

    # STAGE 2: Describe the card with style refs AND rubric for comparison
    _log("[phase grade] ")
    _log("[phase grade] " + "=" * 50)
    _log("[phase grade] STAGE 2: GRADING TEST CARD")
    _log("[phase grade] " + "=" * 50)
    _log(f"[phase grade] Describing card with {len(style_refs)} style refs + rubric...")
    try:
        description = describe_card(out_png, style_refs=style_refs, style_rubric=style_rubric)
    except Exception as e:
        _log(f"[phase grade] Description failed: {e}")
        return 1

    # Check style match
    style_match = description.style_matches_reference
    style_reason = description.style_mismatch_reason or ""

    _log(f"[phase grade] Style match: {style_match}")
    if not style_match:
        _log(f"[phase grade] ⚠️ STYLE MISMATCH: {style_reason}")

    # Score against rubric
    _log(f"[phase grade] Scoring content against rubric...")
    try:
        result = score_against_rubric(description, card_json)
    except Exception as e:
        _log(f"[phase grade] Scoring failed: {e}")
        return 1

    # CRITICAL: Style mismatch = score of 0, automatic fail
    content_score = result.score
    if style_match:
        final_score = content_score
    else:
        final_score = 0  # Style mismatch overrides content score

    passed = style_match and result.passed

    _log(f"[phase grade] Content Score: {content_score}/100")
    _log(f"[phase grade] Final Score: {final_score}/100 {'(style mismatch override)' if not style_match else ''}")
    _log(f"[phase grade] Passed: {passed}")

    if result.corrections:
        _log("[phase grade] Corrections needed:")
        for corr in result.corrections:
            _log(f"  - {corr}")

    # Save grade.json
    grade_json_path = card_dir / "grade.json"
    grade_data = {
        "word": word,
        "card_type": target_type,
        "rarity": target_rarity,
        "content_score": content_score,
        "final_score": final_score,
        "passed": passed,
        "style_matches_reference": style_match,
        "style_mismatch_reason": style_reason,
        "corrections": result.corrections,
        "categories": result.categories,
        "style_refs_count": len(style_refs),
        "style_refs": [Path(r).name for r in style_refs],
    }
    with open(grade_json_path, "w", encoding="utf-8") as f:
        json.dump(grade_data, f, indent=2)
    _log(f"[phase grade] Saved {grade_json_path}")

    # Save grade.txt - match terminal output format
    grade_txt_path = card_dir / "grade.txt"
    status = "PASS" if passed else "FAIL"
    lines = [
        "=" * 60,
        f"GRADE RESULT: {word}",
        "=" * 60,
        f"Score: {final_score}/100" + (f" (content: {content_score}/100)" if not style_match else ""),
        f"Status: {status}",
        f"Style Match: {style_match}",
    ]
    if not style_match:
        lines.append(f"Style Issue: {style_reason}")
    lines.append(f"Style Refs: {len(style_refs)}")
    for ref in style_refs:
        lines.append(f"  - {Path(ref).name}")
    if result.corrections:
        lines.append("")
        lines.append("Corrections Needed:")
        for corr in result.corrections:
            lines.append(f"  - {corr}")
    lines.append("=" * 60)
    with open(grade_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    _log(f"[phase grade] Saved {grade_txt_path}")

    # Print summary (same format as grade.txt)
    print()
    for line in lines:
        print(line)

    return 0 if passed else 1


def phase_review(*, card_dir: Path, max_attempts: int = 2) -> int:
    """
    Multi-stage review of a generated card image with iterative improvement.

    New Flow:
    0. STYLE CHECK: Compare against references - mismatch = auto-fail & rebuild
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
    content = card_json.get("content", {})
    word = content.get("WORD", "UNKNOWN")
    target_rarity = content.get("RARITY", "COMMON")
    target_type = content.get("CARD_TYPE", "NOUN")

    # Get stored style_series_dir from meta.yml (set during initial generation)
    stored_style_series = None
    meta_path = card_dir / "meta.yml"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}
        stored_style_series = meta.get("style_series_dir")

    # Use stored style_series_dir if available, otherwise infer from card path
    if stored_style_series:
        series_dir = Path(stored_style_series)
        _log(f"[phase review] Using stored style_series_dir: {series_dir}")
    else:
        # For demo cards (no stored path), default to the main series with style refs
        if "demo_cards" in str(card_dir) or not (card_dir.parent.parent / "cards").exists():
            series_dir = DEFAULT_SERIES_DIR
            _log(f"[phase review] Demo card detected, using default series: {series_dir}")
        else:
            series_dir = card_dir.parent.parent

    # Check if this is an example card (use templates only, no series cards)
    is_example_card = "example_cards" in str(card_dir)
    if is_example_card:
        _log(f"[phase review] Example card detected - using templates only")

    # Build style references for comparison
    style_refs, _, _ = _build_style_refs(
        series_dir,
        target_rarity=target_rarity,
        target_type=target_type,
        fix_mode=False,
        templates_only=is_example_card,
    )
    _log(f"[phase review] Using {len(style_refs)} style references for comparison")

    # Load static style rubric
    style_rubric = None
    if DEFAULT_STYLE_RUBRIC.exists():
        with open(DEFAULT_STYLE_RUBRIC, "r", encoding="utf-8") as f:
            style_rubric = f.read()
        _log(f"[phase review] Loaded style rubric from {DEFAULT_STYLE_RUBRIC.name}")

    best_score = 0
    best_result: ReviewResult | None = None
    all_descriptions: list[CardDescription] = []
    style_mismatch_count = 0

    for attempt in range(1, max_attempts + 1):
        _log(f"[phase review] === ATTEMPT {attempt}/{max_attempts} for {word} ===")

        # Stage 1: DESCRIBE - Have LLM observe the card (with style refs + rubric for comparison)
        _log(f"[phase review] Stage 1: Describing card with {len(style_refs)} style refs + rubric...")
        try:
            description = describe_card(out_png, style_refs=style_refs, style_rubric=style_rubric)
            all_descriptions.append(description)
        except Exception as e:
            _log(f"[phase review] Description failed: {e}")
            return 1

        # STYLE MISMATCH CHECK - automatic fail if card doesn't match references
        if not description.style_matches_reference:
            style_mismatch_count += 1
            reason = description.style_mismatch_reason or "Style does not match reference cards"
            _log(f"[phase review] ⚠️ STYLE MISMATCH (auto-fail): {reason}")
            print(f"\n{'='*60}")
            print(f"⚠️ STYLE MISMATCH DETECTED - AUTOMATIC FAIL")
            print(f"Reason: {reason}")
            print(f"{'='*60}\n")

            # If this is the last attempt, we're done
            if attempt >= max_attempts:
                _log(f"[phase review] Max attempts reached with style mismatch. Failing card.")
                best_score = 0
                break

            # Rebuild the card with fresh generation
            _log(f"[phase review] Rebuilding card due to style mismatch...")
            try:
                _generate_image_only(card_dir=card_dir)
            except Exception as e:
                _log(f"[phase review] Rebuild failed: {e}")
                return 1
            continue  # Go to next attempt

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
                # No corrections specified, we're at 90+ but not 100 with nothing specific to fix
                _log(f"[phase review] No specific corrections, continuing to polish phase...")

    # Always run polish at the end of review loop (before watermark)
    _log(f"[phase review] Running final polish pass...")
    _run_polish(out_png)

    # Reapply watermark after polish (since polish modifies the image)
    _log(f"[phase review] Reapplying watermark after polish...")
    _run_watermark(card_dir=card_dir, image_path=out_png)

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
            "style_matches_reference": last_desc.style_matches_reference,
            "style_mismatch_reason": last_desc.style_mismatch_reason if not last_desc.style_matches_reference else "",
        }

    # Track style mismatch info
    if style_mismatch_count > 0:
        meta["style_mismatch_count"] = style_mismatch_count
        if all_descriptions:
            # Find first mismatch reason
            for desc in all_descriptions:
                if not desc.style_matches_reference:
                    meta["style_mismatch_reason"] = desc.style_mismatch_reason
                    break

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

    # Write grade.json with detailed results
    # Card passes if score >= 90 AND no style mismatches
    grade_json_path = card_dir / "grade.json"
    passed = best_score >= 90 and style_mismatch_count == 0
    grade_data = {
        "word": word,
        "card_type": target_type,
        "rarity": target_rarity,
        "score": best_score,
        "passed": passed,
        "attempts": max_attempts,
        "style_mismatch_count": style_mismatch_count,
        "corrections": best_result.corrections if best_result else [],
        "categories": best_result.categories if best_result else {},
    }
    with open(grade_json_path, "w", encoding="utf-8") as f:
        json.dump(grade_data, f, indent=2)

    # Write grade.txt with human-readable summary
    grade_txt_path = card_dir / "grade.txt"
    status = "PASS" if passed else "FAIL"
    lines = [
        "CARD GRADE",
        "==========",
        f"Word: {word}",
        f"Type: {target_type}",
        f"Rarity: {target_rarity}",
        f"Score: {best_score}/100",
        f"Status: {status}",
        f"Attempts: {max_attempts}",
        "",
    ]
    if style_mismatch_count > 0:
        lines.append(f"Style Mismatches: {style_mismatch_count}")
    if best_result and best_result.corrections:
        lines.append("Corrections Needed:")
        for c in best_result.corrections:
            lines.append(f"  - {c}")
    with open(grade_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    _log(f"[phase review] Final status: {status_msg}")
    _log(f"[phase review] Wrote grade.json and grade.txt to {card_dir}")
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
        sys.executable, "-m", "hypertext.gallery.builder",
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
    parser.add_argument("--phase", choices=["plan", "imagegen", "demo", "example-cards", "revise", "rebuild", "rebuild-failed", "rebuild-index", "review", "grade", "gallery", "full"], required=True)
    parser.add_argument("--series", default=str(DEFAULT_SERIES_DIR), help="Series directory (for demo phase: output dir)")
    parser.add_argument("--style-series", default=str(DEFAULT_SERIES_DIR), help="Series to use for style references (default: series/2026-Q1)")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE_PATH))
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--batch", type=int, default=1)
    parser.add_argument("--demo-dir", default=str(DEFAULT_DEMO_DIR))
    parser.add_argument("--card-dir")
    parser.add_argument("--revise-file")
    parser.add_argument("--revision", type=str, help="Inline revision instructions (overrides revise.txt)")
    parser.add_argument("--image-only", action="store_true", help="Skip JSON patching, only regenerate image with revision in prompt")
    parser.add_argument("--regen-prompt", action="store_true")
    parser.add_argument("--out-dir", default="_site")
    parser.add_argument("--skip-polish", action="store_true", help="Skip the polish step (bracket removal)")
    parser.add_argument("--skip-watermark", action="store_true", help="Skip watermark generation")
    parser.add_argument("--no-review", action="store_true", help="Skip review/grading phase in demo batch")
    parser.add_argument("--parallel", type=int, default=1, help="Number of cards to generate in parallel (default: 1)")
    parser.add_argument("--card-type", help="For example-cards: generate only this type (NOUN, VERB, ADJECTIVE, NAME, TITLE)")
    parser.add_argument("--rarity", help="For example-cards: generate only this rarity (COMMON, UNCOMMON, RARE, GLORIOUS)")
    parser.add_argument("--count", type=int, default=0, help="For example-cards: max cards to generate (0=all remaining, 1=next card only)")
    parser.add_argument("--ask-before-review", action="store_true", help="Pause after image generation to ask before running review phase")
    parser.add_argument("--style-ref", action="append", dest="style_refs", help="Override style references (repeatable, replaces all programmatic refs)")
    parser.add_argument("--extra-ref", action="append", dest="extra_refs", help="Additional style reference (repeatable, prepended to programmatic refs)")
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
    style_series_dir = Path(args.style_series)
    template_path = Path(args.template)

    batch = int(getattr(args, "batch", 1) or 1)
    if batch < 1:
        batch = 1
    if batch > 100:
        _log(f"[cli] batch clamped from {batch} to 100")
        batch = 100

    parallel = max(1, getattr(args, "parallel", 1) or 1)
    skip_polish = getattr(args, "skip_polish", False)
    skip_watermark = getattr(args, "skip_watermark", False)

    if batch > 1:
        if args.phase == "plan":
            return phase_batch(
                series_dir=series_dir,
                template_path=template_path,
                auto=args.auto,
                batch=batch,
                parallel=parallel,
                skip_polish=skip_polish,
                skip_watermark=skip_watermark,
            )
        if args.phase == "demo":
            return phase_demo_batch(
                style_series_dir=style_series_dir,
                template_path=template_path,
                demo_dir=Path(args.demo_dir),
                batch=batch,
                parallel=parallel,
                skip_polish=skip_polish,
                skip_review=getattr(args, 'no_review', False),
            )
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
        return phase_demo(style_series_dir=style_series_dir, template_path=template_path, demo_dir=Path(args.demo_dir))

    if args.phase == "example-cards":
        example_dir = Path("templates/example_cards")
        override_refs = getattr(args, "style_refs", None) or []
        return phase_example_cards(
            style_series_dir=style_series_dir,
            template_path=template_path,
            example_dir=example_dir,
            parallel=parallel,
            skip_polish=skip_polish,
            target_type=getattr(args, "card_type", None),
            target_rarity=getattr(args, "rarity", None),
            ask_before_review=getattr(args, "ask_before_review", False),
            count=getattr(args, "count", 0) or 0,
            override_style_refs=override_refs if override_refs else None,
        )

    if args.phase == "revise":
        if not args.card_dir:
            print("Missing --card-dir")
            return 2
        revise_file = Path(args.revise_file) if args.revise_file else None
        override_refs = getattr(args, "style_refs", None) or []
        extra_refs = getattr(args, "extra_refs", None) or []
        inline_rev = getattr(args, "revision", None)
        image_only = getattr(args, "image_only", False)
        return phase_revise(
            card_dir=Path(args.card_dir),
            revise_file=revise_file,
            override_style_refs=override_refs if override_refs else None,
            extra_style_refs=extra_refs if extra_refs else None,
            inline_revision=inline_rev,
            image_only=image_only,
        )

    if args.phase == "rebuild":
        if not args.card_dir:
            print("Missing --card-dir")
            return 2
        return phase_rebuild(card_dir=Path(args.card_dir), regen_prompt=bool(args.regen_prompt))

    if args.phase == "rebuild-failed":
        cards_dir = Path(args.demo_dir) if args.demo_dir else DEFAULT_DEMO_DIR
        return phase_rebuild_failed(cards_dir=cards_dir, parallel=args.parallel)

    if args.phase == "rebuild-index":
        _log(f"[rebuild-index] scanning {series_dir} for existing cards...")
        index = _rebuild_cards_index(series_dir)
        print(f"Rebuilt cards index for {series_dir}")
        print(f"  Words: {len(index['words'])}")
        print(f"  Ability patterns: {len(index['ability_patterns'])}")
        print(f"  Cards: {len(index['cards'])}")
        for card in index["cards"]:
            print(f"    #{card['number']:03d} {card['word']} ({card['type']}, {card['rarity']})")
        return 0

    if args.phase == "review":
        if not args.card_dir:
            print("Missing --card-dir")
            return 2
        return phase_review(card_dir=Path(args.card_dir))

    if args.phase == "grade":
        if not args.card_dir:
            print("Missing --card-dir")
            return 2
        return phase_grade(card_dir=Path(args.card_dir), style_series_dir=style_series_dir)

    if args.phase == "gallery":
        return phase_gallery(series_dir=series_dir, out_dir=Path(args.out_dir))

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
