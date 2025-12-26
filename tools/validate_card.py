#!/usr/bin/env python3
"""
Hypertext Card Validator

Validates card.json files against the Hypertext schema and performs
additional lint checks for consistency.

Usage:
    python validate_card.py <card.json>
    python validate_card.py series/2026-Q1/cards/001-magi/card.json
"""

import json
import sys
from pathlib import Path

# Try to import jsonschema for validation
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("Warning: jsonschema not installed. Schema validation disabled.")
    print("Install with: pip install jsonschema")


def load_schema(schema_path: Path) -> dict:
    """Load the JSON schema file."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_card(card_path: Path) -> dict:
    """Load a card.json file."""
    with open(card_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_schema(card: dict, schema: dict) -> list[str]:
    """Validate card against JSON schema."""
    if not HAS_JSONSCHEMA:
        return ["Schema validation skipped (jsonschema not installed)"]

    errors = []
    try:
        jsonschema.validate(card, schema)
    except jsonschema.ValidationError as e:
        errors.append(f"Schema error: {e.message} at {list(e.absolute_path)}")
    except jsonschema.SchemaError as e:
        errors.append(f"Schema definition error: {e.message}")

    return errors


def lint_card(card: dict) -> list[str]:
    """Perform additional lint checks beyond schema validation."""
    errors = []
    warnings = []

    content = card.get('content', {})

    # Check rarity consistency
    rarity_text = content.get('RARITY_TEXT', '')
    rarity_icon = content.get('RARITY_ICON', '')
    if rarity_text and rarity_icon and rarity_text != rarity_icon:
        errors.append(f"RARITY_TEXT ({rarity_text}) does not match RARITY_ICON ({rarity_icon})")

    # Check stat values
    for stat in ['STAT_LORE', 'STAT_CONTEXT', 'STAT_COMPLEXITY']:
        value = content.get(stat)
        if value is not None and (value < 1 or value > 5):
            errors.append(f"{stat} must be between 1 and 5, got {value}")

    # Check trivia count
    trivia = content.get('TRIVIA_BULLETS', [])
    if len(trivia) < 3:
        errors.append(f"TRIVIA_BULLETS must have at least 3 items, got {len(trivia)}")
    elif len(trivia) > 5:
        errors.append(f"TRIVIA_BULLETS must have at most 5 items, got {len(trivia)}")

    # Check card number format
    number = content.get('NUMBER', '')
    if number and (len(number) != 3 or not number.isdigit()):
        errors.append(f"NUMBER must be 3 digits, got '{number}'")

    # Check TITLE card metadata
    card_type = content.get('CARD_TYPE', '')
    if card_type == 'TITLE':
        if not content.get('WILD_ID'):
            warnings.append("TITLE cards should have WILD_ID set")
    else:
        # Non-TITLE cards should have quartet info
        if not content.get('QUARTET_ID') and not content.get('LETTER'):
            pass  # Optional, don't warn

    # Check for empty required strings
    required_strings = ['WORD', 'GLOSS', 'ART_PROMPT', 'ABILITY_TEXT']
    for field in required_strings:
        value = content.get(field, '')
        if not value or not value.strip():
            errors.append(f"{field} is required and cannot be empty")

    # Check art prompt doesn't mention text
    art_prompt = content.get('ART_PROMPT', '').lower()
    text_words = ['text', 'letters', 'words', 'writing', 'label', 'caption']
    for word in text_words:
        if word in art_prompt:
            warnings.append(f"ART_PROMPT contains '{word}' - artwork should not contain text")

    return errors, warnings


def validate_card_file(card_path: Path, schema_path: Path = None) -> tuple[bool, list[str], list[str]]:
    """
    Validate a card.json file.

    Returns:
        (is_valid, errors, warnings)
    """
    errors = []
    warnings = []

    # Determine schema path
    if schema_path is None:
        # Look for schema relative to card path
        repo_root = card_path.parent
        while repo_root.parent != repo_root:
            candidate = repo_root / 'schema' / 'hypertext_card.schema.json'
            if candidate.exists():
                schema_path = candidate
                break
            repo_root = repo_root.parent

    # Load card
    try:
        card = load_card(card_path)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"], []
    except FileNotFoundError:
        return False, [f"File not found: {card_path}"], []

    # Schema validation
    if schema_path and schema_path.exists():
        schema = load_schema(schema_path)
        schema_errors = validate_schema(card, schema)
        errors.extend(schema_errors)
    else:
        warnings.append("Schema file not found, skipping schema validation")

    # Lint checks
    lint_errors, lint_warnings = lint_card(card)
    errors.extend(lint_errors)
    warnings.extend(lint_warnings)

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    card_path = Path(sys.argv[1])
    schema_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    is_valid, errors, warnings = validate_card_file(card_path, schema_path)

    # Print results
    print(f"\nValidating: {card_path}")
    print("=" * 60)

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  [WARN] {w}")

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  [ERROR] {e}")

    if is_valid:
        print("\n[OK] Card is valid!")
        sys.exit(0)
    else:
        print(f"\n[FAIL] Card has {len(errors)} error(s)")
        sys.exit(1)


if __name__ == '__main__':
    main()
