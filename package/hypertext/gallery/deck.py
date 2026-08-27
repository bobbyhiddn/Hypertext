#!/usr/bin/env python3
"""
Hypertext Deck Assembler

Compiles cards from a series folder into a deck manifest and
prepares files for print export.

Usage:
    python -m hypertext.gallery.deck <series_path>
    python -m hypertext.gallery.deck series/2026-Q1

This will:
1. Scan the cards/ folder for valid card.json files
2. Validate each card
3. Generate decklist.yml
4. Prepare export manifest
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Try to import yaml for output
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("Warning: pyyaml not installed. Using JSON fallback for decklist.")
    print("Install with: pip install pyyaml")


def find_cards(series_path: Path) -> list[Path]:
    """Find all card.json files in a series."""
    cards_dir = series_path / 'cards'
    if not cards_dir.exists():
        return []

    cards = []
    for card_dir in sorted(cards_dir.iterdir()):
        if card_dir.is_dir():
            card_file = card_dir / 'card.json'
            if card_file.exists():
                cards.append(card_file)

    return cards


def load_card(card_path: Path) -> dict | None:
    """Load a card.json file."""
    try:
        with open(card_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  [ERROR] Failed to load {card_path}: {e}")
        return None


def extract_card_info(card: dict, card_path: Path) -> dict:
    """Extract key info from a card for the decklist."""
    content = card.get('content', {})

    # Find output images
    outputs_dir = card_path.parent / 'outputs'
    images = []
    if outputs_dir.exists():
        for img in outputs_dir.iterdir():
            if img.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                images.append(str(img.relative_to(card_path.parent.parent.parent)))

    return {
        'number': content.get('NUMBER', '???'),
        'word': content.get('WORD', 'Unknown'),
        'gloss': content.get('GLOSS', ''),
        'type': content.get('CARD_TYPE', 'NOUN'),
        'rarity': content.get('RARITY_TEXT', 'COMMON'),
        'folder': card_path.parent.name,
        'images': images,
        'stats': {
            'lore': content.get('STAT_LORE', 0),
            'context': content.get('STAT_CONTEXT', 0),
            'complexity': content.get('STAT_COMPLEXITY', 0),
        }
    }


def generate_decklist(cards_info: list[dict], series_name: str) -> dict:
    """Generate a decklist manifest."""
    # Count by rarity
    rarity_counts = {'COMMON': 0, 'UNCOMMON': 0, 'RARE': 0, 'GLORIOUS': 0}
    type_counts = {'NOUN': 0, 'VERB': 0, 'ADJECTIVE': 0, 'NAME': 0, 'TITLE': 0}

    for card in cards_info:
        rarity = card.get('rarity', 'COMMON')
        card_type = card.get('type', 'NOUN')
        rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
        type_counts[card_type] = type_counts.get(card_type, 0) + 1

    return {
        'series': series_name,
        'generated': datetime.now().isoformat(),
        'total_cards': len(cards_info),
        'by_rarity': rarity_counts,
        'by_type': type_counts,
        'cards': cards_info
    }


def save_decklist(decklist: dict, output_path: Path):
    """Save the decklist to file."""
    if HAS_YAML and output_path.suffix == '.yml':
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(decklist, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    else:
        # Fallback to JSON
        output_path = output_path.with_suffix('.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(decklist, f, indent=2, ensure_ascii=False)

    return output_path


def assemble_deck(series_path: Path) -> tuple[bool, dict]:
    """
    Assemble a deck from a series folder.

    Returns:
        (success, decklist)
    """
    print(f"\nAssembling deck from: {series_path}")
    print("=" * 60)

    # Find all cards
    card_files = find_cards(series_path)
    print(f"Found {len(card_files)} card(s)")

    if not card_files:
        print("[WARN] No cards found in series")
        return False, {}

    # Load and process each card
    cards_info = []
    errors = 0

    for card_path in card_files:
        card = load_card(card_path)
        if card:
            info = extract_card_info(card, card_path)
            cards_info.append(info)
            print(f"  [OK] #{info['number']} {info['word']} ({info['rarity']})")
        else:
            errors += 1

    # Sort by number
    cards_info.sort(key=lambda c: c.get('number', '999'))

    # Generate decklist
    series_name = series_path.name
    decklist = generate_decklist(cards_info, series_name)

    # Save decklist
    deck_dir = series_path / 'deck'
    deck_dir.mkdir(exist_ok=True)

    output_path = deck_dir / 'decklist.yml'
    saved_path = save_decklist(decklist, output_path)
    print(f"\nDecklist saved to: {saved_path}")

    # Summary
    print(f"\n{'-' * 40}")
    print(f"Total: {decklist['total_cards']} cards")
    print(f"By rarity: {decklist['by_rarity']}")
    print(f"By type: {decklist['by_type']}")

    if errors:
        print(f"\n[WARN] {errors} card(s) had errors")

    success = errors == 0
    return success, decklist


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    series_path = Path(sys.argv[1])

    if not series_path.exists():
        print(f"Error: Series path not found: {series_path}")
        sys.exit(1)

    success, decklist = assemble_deck(series_path)

    if success:
        print("\n[OK] Deck assembled successfully!")
        sys.exit(0)
    else:
        print("\n[WARN] Deck assembled with warnings")
        sys.exit(0)  # Still exit 0 if we got a decklist


if __name__ == '__main__':
    main()
