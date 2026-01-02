#!/usr/bin/env python3
"""Debug sprite sheet and card issues."""

from pathlib import Path
from PIL import Image

# Check sprite sheet dimensions
sprite_path = Path("series/2026-Q1/exports/tabletopsimulator/main_deck_sheet.png")
if sprite_path.exists():
    img = Image.open(sprite_path)
    print(f"Sprite sheet size: {img.size}")
    print(f"Expected for 90 cards (10x9): {409*10}x{585*9} = (4090, 5265)")

    cols = img.width // 409
    rows = img.height // 585
    print(f"Actual grid: {cols}x{rows} = {cols * rows} card slots")

    # Check if card 70 position has content (not black)
    card_70_x = (70 % 10) * 409
    card_70_y = (70 // 10) * 585
    pixel = img.getpixel((card_70_x + 200, card_70_y + 200))
    print(f"\nCard 70 position ({card_70_x}, {card_70_y}), sample pixel: {pixel}")
    if pixel == (30, 30, 30) or pixel == (0, 0, 0):
        print("  -> Card 70 appears to be placeholder/empty!")
    else:
        print("  -> Card 70 has image content")

    # Check card 89
    card_89_x = (89 % 10) * 409
    card_89_y = (89 // 10) * 585
    pixel = img.getpixel((card_89_x + 200, card_89_y + 200))
    print(f"Card 89 position ({card_89_x}, {card_89_y}), sample pixel: {pixel}")
    if pixel == (30, 30, 30) or pixel == (0, 0, 0):
        print("  -> Card 89 appears to be placeholder/empty!")
    else:
        print("  -> Card 89 has image content")
else:
    print(f"Sprite sheet not found: {sprite_path}")

# Check which demo_cards have images
print("\nChecking demo_cards images (cards 65-90):")
demo_cards = Path("demo_cards")
card_dirs = sorted([d for d in demo_cards.iterdir() if d.is_dir() and d.name[0].isdigit()])

missing = []
for i, card_dir in enumerate(card_dirs[:90]):
    img_path = card_dir / "outputs" / "card_1024x1536.png"
    if not img_path.exists():
        missing.append((i, card_dir.name))
        if i >= 65:
            print(f"  [{i}] {card_dir.name}: MISSING")

print(f"\nTotal missing: {len(missing)} cards")
for i, name in missing:
    print(f"  [{i}] {name}")
