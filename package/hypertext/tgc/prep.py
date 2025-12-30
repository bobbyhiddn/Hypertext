#!/usr/bin/env python3
"""
Prepare Hypertext cards for manual TGC upload.

Creates batched folders of print-ready images for manual upload to TGC.
Batches are limited to 25 cards to match TGC's upload interface.

Usage:
  # Prep cards from demo_cards
  python -m hypertext.tgc prep --cards-dir demo_cards

  # Prep cards from a series
  python -m hypertext.tgc prep --cards-dir series/2026-Q1/cards

  # Prep with lots included
  python -m hypertext.tgc prep --cards-dir series/2026-Q1/cards --lots-dir series/2026-Q1/lots

  # Limit number of cards
  python -m hypertext.tgc prep --cards-dir demo_cards --limit 50
"""

import argparse
import logging
import shutil
from pathlib import Path

from PIL import Image

from .processor import prepare_for_print, PRINT_WIDTH, PRINT_HEIGHT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 25
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"


def find_card_images(cards_dir: Path, limit: int = 0) -> list[Path]:
    """Find card images in a directory structure."""
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

    return card_images


def find_lot_images(lots_dir: Path, limit: int = 0) -> list[Path]:
    """Find lot images in a directory structure."""
    lot_images = []

    logger.debug(f"Searching for lots in: {lots_dir}")
    for lot_dir in sorted(lots_dir.iterdir()):
        if not lot_dir.is_dir():
            continue
        if not lot_dir.name[0].isdigit():
            logger.debug(f"  Skipping {lot_dir.name} (doesn't start with digit)")
            continue

        outputs_dir = lot_dir / "outputs"
        if outputs_dir.exists():
            for pattern in ["lot_1024x1536.png", "lot_*.png", "*.png"]:
                matches = list(outputs_dir.glob(pattern))
                if matches:
                    lot_images.append(matches[0])
                    logger.debug(f"  Found: {matches[0]}")
                    break
        else:
            logger.debug(f"  No outputs dir in {lot_dir.name}")

    if limit > 0:
        lot_images = lot_images[:limit]

    return lot_images


def process_and_batch(
    images: list[Path],
    output_dir: Path,
    prefix: str,
) -> int:
    """Process images and organize into batches of 25.

    Args:
        images: List of source image paths
        output_dir: Base output directory (e.g., tgc_prep/cards/)
        prefix: Filename prefix (e.g., "card" or "lot")

    Returns:
        Number of batches created
    """
    if not images:
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)

    total_batches = (len(images) + BATCH_SIZE - 1) // BATCH_SIZE
    logger.info(f"Processing {len(images)} {prefix}s into {total_batches} batch(es)...")

    for batch_num in range(total_batches):
        batch_start = batch_num * BATCH_SIZE
        batch_end = min(batch_start + BATCH_SIZE, len(images))
        batch_images = images[batch_start:batch_end]

        batch_dir = output_dir / f"batch_{batch_num + 1:02d}"
        batch_dir.mkdir(parents=True, exist_ok=True)

        # Process each card in the batch
        for i, img_path in enumerate(batch_images):
            card_num = batch_start + i + 1
            output_name = f"{prefix}_{card_num:03d}.png"
            output_path = batch_dir / output_name

            try:
                img = Image.open(img_path)
                processed = prepare_for_print(img)
                processed.save(output_path, "PNG")
                logger.debug(f"  {img_path.name} -> {output_name}")
            except Exception as e:
                logger.error(f"Failed to process {img_path}: {e}")

        logger.info(f"  Batch {batch_num + 1}: {len(batch_images)} {prefix}s -> {batch_dir}")

    return total_batches


def prep_command(args: argparse.Namespace) -> int:
    """Execute the prep command."""
    # Determine source directories (resolve to absolute paths)
    cards_dir = args.cards_dir.resolve() if args.cards_dir else None
    lots_dir = args.lots_dir.resolve() if args.lots_dir else None

    if not cards_dir and not lots_dir:
        cards_dir = PROJECT_ROOT / "demo_cards"
        logger.info(f"No directories specified, using {cards_dir}")

    # Auto-detect lots directory
    if cards_dir and not lots_dir:
        # Check for sibling lots/ directory (series structure)
        sibling_lots = cards_dir.parent / "lots"
        if sibling_lots.exists():
            lots_dir = sibling_lots
            logger.info(f"Auto-detected lots directory: {lots_dir}")
        else:
            # For demo_cards or other non-series dirs, use Series 1 lots
            series1_lots = PROJECT_ROOT / "series" / "2026-Q1" / "lots"
            if series1_lots.exists():
                lots_dir = series1_lots
                logger.info(f"Using Series 1 lots: {lots_dir}")

    # Determine output directory
    if args.output_dir:
        output_base = args.output_dir
    elif cards_dir:
        output_base = cards_dir / "tgc_prep"
    else:
        output_base = lots_dir / "tgc_prep"

    # Clean output directory if it exists
    if output_base.exists() and not args.no_clean:
        logger.info(f"Cleaning existing output: {output_base}")
        shutil.rmtree(output_base)

    output_base.mkdir(parents=True, exist_ok=True)

    # Find images
    card_images = []
    lot_images = []

    if cards_dir and cards_dir.exists():
        card_images = find_card_images(cards_dir, args.limit)
        logger.info(f"Found {len(card_images)} cards in {cards_dir}")

    if lots_dir and lots_dir.exists():
        lot_images = find_lot_images(lots_dir, args.limit)
        logger.info(f"Found {len(lot_images)} lots in {lots_dir}")

    if not card_images and not lot_images:
        logger.error("No card or lot images found")
        return 1

    # Process cards
    card_batches = 0
    if card_images:
        card_batches = process_and_batch(
            card_images,
            output_base / "cards",
            "card",
        )

        # Process card back
        card_back = TEMPLATES_DIR / "card_back.png"
        if card_back.exists():
            back_dir = output_base / "cards" / "back"
            back_dir.mkdir(parents=True, exist_ok=True)
            back_output = back_dir / "card_back.png"
            logger.info(f"Processing card back -> {back_output}")
            img = Image.open(card_back)
            processed = prepare_for_print(img)
            processed.save(back_output, "PNG")

    # Process lots
    lot_batches = 0
    if lot_images:
        lot_batches = process_and_batch(
            lot_images,
            output_base / "lots",
            "lot",
        )

        # Process lot back
        lot_back = TEMPLATES_DIR / "lots" / "Lot_Back.png"
        if lot_back.exists():
            back_dir = output_base / "lots" / "back"
            back_dir.mkdir(parents=True, exist_ok=True)
            back_output = back_dir / "lot_back.png"
            logger.info(f"Processing lot back -> {back_output}")
            img = Image.open(lot_back)
            processed = prepare_for_print(img)
            processed.save(back_output, "PNG")

    # Summary
    logger.info("")
    logger.info("=== TGC Prep Complete ===")
    logger.info(f"Output: {output_base}")
    if card_images:
        logger.info(f"Cards: {len(card_images)} images in {card_batches} batch(es)")
    if lot_images:
        logger.info(f"Lots: {len(lot_images)} images in {lot_batches} batch(es)")
    logger.info(f"Image size: {PRINT_WIDTH}x{PRINT_HEIGHT} (TGC poker card)")
    logger.info("")
    logger.info("Upload each batch folder to TGC manually.")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Prepare Hypertext cards for manual TGC upload",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Prep series cards (auto-detects sibling lots/ directory)
  python -m hypertext.tgc prep --cards-dir series/2026-Q1/cards

  # Prep demo cards only
  python -m hypertext.tgc prep --cards-dir demo_cards

  # Limit to first 10 cards
  python -m hypertext.tgc prep --cards-dir series/2026-Q1/cards --limit 10
        """
    )

    parser.add_argument(
        "--cards-dir",
        type=Path,
        help="Directory containing card folders",
    )
    parser.add_argument(
        "--lots-dir",
        type=Path,
        help="Directory containing lot folders (auto-detected as sibling if not specified)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (default: <parent>/tgc_prep)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum images to process (0 = all)",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Don't clean existing output directory",
    )

    args = parser.parse_args()
    return prep_command(args)


if __name__ == "__main__":
    exit(main())
