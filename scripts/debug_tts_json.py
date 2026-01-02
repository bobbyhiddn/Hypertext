#!/usr/bin/env python3
"""Debug TTS JSON deck configuration."""

import json
from pathlib import Path

json_path = Path("series/2026-Q1/exports/tabletopsimulator/Hypertext.json")
if not json_path.exists():
    print(f"JSON not found: {json_path}")
    exit(1)

with open(json_path) as f:
    data = json.load(f)

print("TTS JSON Analysis:")
print("=" * 50)

for obj in data.get("ObjectStates", []):
    name = obj.get("Nickname", obj.get("Name", "Unknown"))

    if obj.get("Name") == "DeckCustom":
        print(f"\nDeck: {name}")

        custom_deck = obj.get("CustomDeck", {})
        for deck_id, deck_info in custom_deck.items():
            print(f"  Deck ID: {deck_id}")
            print(f"  FaceURL: {deck_info.get('FaceURL', 'MISSING')[:80]}...")
            print(f"  BackURL: {deck_info.get('BackURL', 'MISSING')[:80]}...")
            print(f"  NumWidth: {deck_info.get('NumWidth')}")
            print(f"  NumHeight: {deck_info.get('NumHeight')}")

            # Check if NumWidth * NumHeight >= card count
            num_w = deck_info.get('NumWidth', 0)
            num_h = deck_info.get('NumHeight', 0)
            max_cards = num_w * num_h
            print(f"  Max cards (NumWidth x NumHeight): {max_cards}")

        deck_ids = obj.get("DeckIDs", [])
        print(f"  DeckIDs count: {len(deck_ids)}")
        if deck_ids:
            print(f"  DeckIDs range: {min(deck_ids)} - {max(deck_ids)}")

        contained = obj.get("ContainedObjects", [])
        print(f"  ContainedObjects count: {len(contained)}")

        # Check if any CardID exceeds the sprite sheet
        if deck_ids and custom_deck:
            deck_id = list(custom_deck.keys())[0]
            base = int(deck_id) * 100
            num_w = custom_deck[deck_id].get('NumWidth', 10)
            num_h = custom_deck[deck_id].get('NumHeight', 10)
            max_index = num_w * num_h - 1

            for card_id in deck_ids:
                index = card_id - base
                if index > max_index:
                    print(f"  WARNING: CardID {card_id} (index {index}) exceeds sprite sheet size ({max_index})")
