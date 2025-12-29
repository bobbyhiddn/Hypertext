#!/usr/bin/env python3
"""
Upload Hypertext cards to The Game Crafter.

This script uploads card images to TGC, creates a game project, and stages
Poker Decks for ordering. Supports both main deck and lots (phase cards).

Usage:
  # Upload main deck only
  python -m hypertext.tgc --cards-dir demo_cards

  # Upload both main deck and lots
  python -m hypertext.tgc --cards-dir demo_cards --lots-dir series/2026-Q1/lots

  # Full example with all options
  python -m hypertext.tgc \\
    --cards-dir demo_cards \\
    --card-back templates/card_back.png \\
    --lots-dir series/2026-Q1/lots \\
    --lot-back templates/lot_back.png \\
    --game-name "Hypertext Core Set"

  # Dry run (process images locally, no upload)
  python -m hypertext.tgc --cards-dir demo_cards --lots-dir series/2026-Q1/lots --dry-run

Environment variables required:
  TGC_API_KEY - API Key from TGC Developer settings
  TGC_USERNAME - TGC account username
  TGC_PASSWORD - TGC account password
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

from .client import TGCClient, TGCError
from .processor import prepare_for_print, PRINT_WIDTH, PRINT_HEIGHT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
CARD_BACK_PATH = TEMPLATES_DIR / "card_back.png"
LOT_BACK_PATH = TEMPLATES_DIR / "lots" / "Lot_Back.png"


def find_card_images(cards_dir: Path, limit: int = 0) -> list[Path]:
    """Find card images in a directory structure.

    Looks for card_1024x1536.png in card subdirectories.

    Args:
        cards_dir: Directory containing card folders
        limit: Maximum cards to return (0 = no limit)

    Returns:
        List of paths to card images, sorted by card number
    """
    card_images = []

    for card_dir in sorted(cards_dir.iterdir()):
        if not card_dir.is_dir():
            continue
        if not card_dir.name[0].isdigit():
            continue

        outputs_dir = card_dir / "outputs"
        if outputs_dir.exists():
            for pattern in ["card_1024x1536.png", "card_*.png", "*.png"]:
                matches = list(outputs_dir.glob(pattern))
                if matches:
                    card_images.append(matches[0])
                    break

    if limit > 0:
        card_images = card_images[:limit]

    logger.info(f"Found {len(card_images)} card images in {cards_dir}")
    return card_images


def find_lot_images(lots_dir: Path, limit: int = 0) -> list[Path]:
    """Find lot (phase card) images in a directory structure.

    Looks for lot_1024x1536.png in lot subdirectories.

    Args:
        lots_dir: Directory containing lot folders
        limit: Maximum lots to return (0 = no limit)

    Returns:
        List of paths to lot images, sorted by lot number
    """
    lot_images = []

    for lot_dir in sorted(lots_dir.iterdir()):
        if not lot_dir.is_dir():
            continue
        if not lot_dir.name[0].isdigit():
            continue

        outputs_dir = lot_dir / "outputs"
        if outputs_dir.exists():
            for pattern in ["lot_1024x1536.png", "lot_*.png", "*.png"]:
                matches = list(outputs_dir.glob(pattern))
                if matches:
                    lot_images.append(matches[0])
                    break

    if limit > 0:
        lot_images = lot_images[:limit]

    logger.info(f"Found {len(lot_images)} lot images in {lots_dir}")
    return lot_images


def load_manifest(manifest_path: Path) -> dict:
    """Load or create a manifest."""
    if manifest_path.exists():
        with open(manifest_path) as f:
            return json.load(f)

    return {
        "version": "1.0.0",
        "generated_at": None,
        "tgc_game_id": None,
        "tgc_folder_id": None,
        "main_deck": {
            "name": "Main Deck",
            "tgc_deck_id": None,
            "tgc_back_file_id": None,
            "cards": [],
        },
        "lots_deck": {
            "name": "Phase Cards",
            "tgc_deck_id": None,
            "tgc_back_file_id": None,
            "cards": [],
        },
    }


def save_manifest(manifest: dict, manifest_path: Path) -> None:
    """Save manifest to file."""
    manifest["generated_at"] = datetime.utcnow().isoformat() + "Z"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Saved manifest to {manifest_path}")


def upload_deck(
    client: TGCClient,
    card_images: list[Path],
    card_back_path: Path,
    deck_name: str,
    card_prefix: str,
    game_id: str,
    folder_id: str,
    print_dir: Path,
    deck_manifest: dict,
) -> dict:
    """Upload a single deck to TGC.

    Args:
        client: Authenticated TGC client
        card_images: List of card image paths
        card_back_path: Path to card back image
        deck_name: Name for the poker deck
        card_prefix: Prefix for card IDs (e.g., "HT" or "LOT")
        game_id: TGC game ID
        folder_id: TGC folder ID
        print_dir: Directory for processed print images
        deck_manifest: Deck section of manifest to update

    Returns:
        Updated deck manifest
    """
    if Image is None:
        raise TGCError("Pillow required: pip install pillow")

    # Process and upload card back
    back_filename = f"{card_prefix.lower()}_back_print.png"
    back_print_path = print_dir / back_filename

    if not back_print_path.exists():
        logger.info(f"Processing {deck_name} card back for print...")
        back_img = Image.open(card_back_path)
        back_print = prepare_for_print(back_img)
        back_print.save(back_print_path, "PNG")

    back_file_id = deck_manifest.get("tgc_back_file_id")
    if not back_file_id:
        logger.info(f"Uploading {deck_name} card back...")
        back_file_id = client.upload_file(back_print_path, folder_id, f"{card_prefix.lower()}_back.png")
        deck_manifest["tgc_back_file_id"] = back_file_id

    # Get or create deck
    deck_id = deck_manifest.get("tgc_deck_id")
    if not deck_id:
        deck_id = client.create_poker_deck(game_id, deck_name, back_file_id)
        deck_manifest["tgc_deck_id"] = deck_id
    else:
        logger.info(f"Clearing existing cards from {deck_name}...")
        client.clear_deck(deck_id)

    # Build card manifest entries if empty
    if not deck_manifest["cards"]:
        for i, img_path in enumerate(card_images):
            card_id = f"{card_prefix}-{i+1:03d}"
            deck_manifest["cards"].append({
                "id": card_id,
                "source_path": str(img_path),
                "print_path": None,
                "tgc_file_id": None,
            })

    # Process and upload each card
    face_file_ids = []

    for i, card_entry in enumerate(deck_manifest["cards"]):
        source_path = Path(card_entry["source_path"])

        if not source_path.exists():
            logger.warning(f"Card image not found: {source_path}")
            continue

        # Check if already uploaded
        if card_entry.get("tgc_file_id"):
            logger.info(f"Card {card_entry['id']} already uploaded, skipping...")
            face_file_ids.append(card_entry["tgc_file_id"])
            continue

        # Process for print
        print_path = print_dir / f"{card_entry['id']}.png"
        if not print_path.exists():
            logger.info(f"Processing {card_entry['id']} for print...")
            card_img = Image.open(source_path)
            card_print = prepare_for_print(card_img)
            card_print.save(print_path, "PNG")
        card_entry["print_path"] = str(print_path)

        # Upload to TGC
        logger.info(f"Uploading {card_entry['id']}...")
        file_id = client.upload_file(print_path, folder_id, f"{card_entry['id']}.png")
        card_entry["tgc_file_id"] = file_id
        face_file_ids.append(file_id)

    # Add all cards to deck in batch
    if face_file_ids:
        logger.info(f"Adding {len(face_file_ids)} cards to {deck_name}...")
        client.add_cards_batch(deck_id, face_file_ids)

    deck_manifest["name"] = deck_name
    return deck_manifest


def process_images_dry_run(
    card_images: list[Path],
    card_prefix: str,
    print_dir: Path,
) -> None:
    """Process images for print without uploading."""
    if Image is None:
        raise TGCError("Pillow required for image processing")

    print_dir.mkdir(parents=True, exist_ok=True)

    for i, img_path in enumerate(card_images):
        card_id = f"{card_prefix}-{i+1:03d}"
        print_path = print_dir / f"{card_id}.png"

        if print_path.exists():
            logger.info(f"Already processed: {print_path.name}")
            continue

        logger.info(f"Processing {img_path.name} -> {card_id}...")
        img = Image.open(img_path)
        processed = prepare_for_print(img)
        processed.save(print_path, "PNG")

    logger.info(f"Processed {len(card_images)} cards to {print_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Upload Hypertext cards to The Game Crafter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Main deck only
  python -m hypertext.tgc --cards-dir demo_cards

  # Both decks
  python -m hypertext.tgc --cards-dir demo_cards --lots-dir series/2026-Q1/lots

  # Dry run (no upload)
  python -m hypertext.tgc --cards-dir demo_cards --dry-run
        """
    )

    # Main deck options
    parser.add_argument(
        "--cards-dir",
        type=Path,
        help="Directory containing main deck card folders",
    )
    parser.add_argument(
        "--card-back",
        type=Path,
        default=CARD_BACK_PATH,
        help="Path to main deck card back image",
    )
    parser.add_argument(
        "--card-limit",
        type=int,
        default=0,
        help="Maximum main deck cards to upload (0 = all)",
    )

    # Lots deck options
    parser.add_argument(
        "--lots-dir",
        type=Path,
        help="Directory containing lot (phase card) folders",
    )
    parser.add_argument(
        "--lot-back",
        type=Path,
        default=LOT_BACK_PATH,
        help="Path to lot deck card back image",
    )
    parser.add_argument(
        "--lot-limit",
        type=int,
        default=0,
        help="Maximum lot cards to upload (0 = all)",
    )

    # Game options
    parser.add_argument(
        "--game-name",
        default="Hypertext",
        help="Name for TGC game project",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for processed images and manifest",
    )

    # Mode options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process images but don't upload to TGC",
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.cards_dir and not args.lots_dir:
        # Default to demo_cards
        args.cards_dir = PROJECT_ROOT / "demo_cards"
        logger.info(f"No --cards-dir specified, using {args.cards_dir}")

    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    elif args.cards_dir:
        output_dir = args.cards_dir / "exports" / "tgc"
    else:
        output_dir = PROJECT_ROOT / "exports" / "tgc"

    print_dir = output_dir / "print"
    print_dir.mkdir(parents=True, exist_ok=True)

    # Find images
    card_images = []
    lot_images = []

    if args.cards_dir:
        card_images = find_card_images(args.cards_dir, args.card_limit)

    if args.lots_dir:
        lot_images = find_lot_images(args.lots_dir, args.lot_limit)

    if not card_images and not lot_images:
        logger.error("No card or lot images found")
        sys.exit(1)

    # Dry run mode
    if args.dry_run:
        logger.info("=== DRY RUN MODE - Processing images only ===")

        if card_images:
            logger.info(f"\n--- Processing {len(card_images)} main deck cards ---")
            process_images_dry_run(card_images, "HT", print_dir / "main")

        if lot_images:
            logger.info(f"\n--- Processing {len(lot_images)} lot cards ---")
            process_images_dry_run(lot_images, "LOT", print_dir / "lots")

        logger.info(f"\nProcessed images saved to {print_dir}")
        return

    # Check card backs exist
    if card_images and not args.card_back.exists():
        logger.error(f"Card back not found: {args.card_back}")
        sys.exit(1)

    if lot_images and not args.lot_back.exists():
        logger.error(f"Lot back not found: {args.lot_back}")
        logger.info("Create lot_back.png or specify --lot-back path")
        sys.exit(1)

    # Load manifest
    manifest_path = output_dir / "tgc_manifest.json"
    manifest = load_manifest(manifest_path)

    # Initialize TGC client
    try:
        client = TGCClient()
        client.authenticate()
    except TGCError as e:
        logger.error(f"TGC authentication failed: {e}")
        sys.exit(1)

    try:
        # Create folder for this project
        folder_id = manifest.get("tgc_folder_id")
        if not folder_id:
            folder_id = client.get_or_create_folder("Hypertext")
            manifest["tgc_folder_id"] = folder_id

        # Get or create game
        game_id = manifest.get("tgc_game_id")
        if not game_id:
            game_id = client.get_or_create_game(
                args.game_name,
                "Biblical word-study trading card game"
            )
            manifest["tgc_game_id"] = game_id

        # Upload main deck
        if card_images:
            logger.info(f"\n=== Uploading Main Deck ({len(card_images)} cards) ===")
            manifest["main_deck"] = upload_deck(
                client=client,
                card_images=card_images,
                card_back_path=args.card_back,
                deck_name="Main Deck",
                card_prefix="HT",
                game_id=game_id,
                folder_id=folder_id,
                print_dir=print_dir / "main",
                deck_manifest=manifest.get("main_deck", {}),
            )

        # Upload lots deck
        if lot_images:
            logger.info(f"\n=== Uploading Lots Deck ({len(lot_images)} cards) ===")
            manifest["lots_deck"] = upload_deck(
                client=client,
                card_images=lot_images,
                card_back_path=args.lot_back,
                deck_name="Phase Cards",
                card_prefix="LOT",
                game_id=game_id,
                folder_id=folder_id,
                print_dir=print_dir / "lots",
                deck_manifest=manifest.get("lots_deck", {}),
            )

        save_manifest(manifest, manifest_path)

        # Summary
        logger.info("\n=== Upload Complete ===")
        logger.info(f"Game ID: {manifest['tgc_game_id']}")

        if card_images:
            main_uploaded = len([c for c in manifest["main_deck"]["cards"] if c.get("tgc_file_id")])
            logger.info(f"Main Deck: {main_uploaded} cards (ID: {manifest['main_deck']['tgc_deck_id']})")

        if lot_images:
            lots_uploaded = len([c for c in manifest["lots_deck"]["cards"] if c.get("tgc_file_id")])
            logger.info(f"Lots Deck: {lots_uploaded} cards (ID: {manifest['lots_deck']['tgc_deck_id']})")

        logger.info("\nVisit https://www.thegamecrafter.com/games to view your game")

    except TGCError as e:
        logger.error(f"Upload failed: {e}")
        save_manifest(manifest, manifest_path)
        sys.exit(1)


if __name__ == "__main__":
    main()
