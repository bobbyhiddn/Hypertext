#!/usr/bin/env python3
"""
Export Hypertext cards to print-ready PDF sheets for Office Depot/OfficeMax.

Creates letter-size (8.5" x 11") PDF with 6 cards per page at 93% scale,
suitable for printing on 110 lb cardstock.

Usage:
  python -m hypertext.tgc print --cards-dir demo_cards
  python -m hypertext.tgc print --cards-dir demo_cards --output prints/playtest.pdf
"""

import argparse
import logging
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

# Page specifications at 300 DPI
DPI = 300
LETTER_WIDTH_IN = 8.5
LETTER_HEIGHT_IN = 11.0
LETTER_WIDTH_PX = int(LETTER_WIDTH_IN * DPI)   # 2550
LETTER_HEIGHT_PX = int(LETTER_HEIGHT_IN * DPI)  # 3300

# Unprintable margin (Office Depot laser printer)
MARGIN_IN = 0.25
MARGIN_PX = int(MARGIN_IN * DPI)  # 75

# Safe printable area
SAFE_WIDTH_PX = LETTER_WIDTH_PX - (2 * MARGIN_PX)   # 2400
SAFE_HEIGHT_PX = LETTER_HEIGHT_PX - (2 * MARGIN_PX)  # 3150

# Source card size (TGC poker card)
CARD_WIDTH_PX = 825
CARD_HEIGHT_PX = 1125

# Scaled card size (90% to fit 3x3 grid)
SCALE = 0.90
SCALED_CARD_WIDTH = int(CARD_WIDTH_PX * SCALE)   # 742
SCALED_CARD_HEIGHT = int(CARD_HEIGHT_PX * SCALE)  # 1012

# Layout: 3 columns x 3 rows = 9 cards per page
COLS = 3
ROWS = 3
CARDS_PER_PAGE = COLS * ROWS

# Gutter between cards
GUTTER_PX = int(0.125 * DPI)  # 38px (~0.125")

# Cut guide color
CUT_GUIDE_COLOR = (200, 200, 200)  # Light gray


def find_card_images(cards_dir: Path, limit: int = 0) -> list[Path]:
    """Find card images in tgc_prep or outputs directories."""
    card_images = []

    # First check for tgc_prep/cards structure
    tgc_prep = cards_dir / "tgc_prep" / "cards"
    if tgc_prep.exists():
        for batch_dir in sorted(tgc_prep.iterdir()):
            if batch_dir.is_dir() and batch_dir.name.startswith("batch_"):
                for img in sorted(batch_dir.glob("card_*.png")):
                    card_images.append(img)
        if card_images:
            logger.info(f"Found {len(card_images)} cards in tgc_prep")
            if limit > 0:
                card_images = card_images[:limit]
            return card_images

    # Fall back to standard card directory structure
    for card_dir in sorted(cards_dir.iterdir()):
        if not card_dir.is_dir():
            continue
        if not card_dir.name[0].isdigit():
            continue

        outputs_dir = card_dir / "outputs"
        if outputs_dir.exists():
            for pattern in ["card_1024x1536.png", "card_*.png"]:
                matches = list(outputs_dir.glob(pattern))
                if matches:
                    card_images.append(matches[0])
                    break

    if limit > 0:
        card_images = card_images[:limit]

    logger.info(f"Found {len(card_images)} cards in {cards_dir}")
    return card_images


def create_back_page(
    back_image: Image.Image,
    num_cards: int,
    draw_cut_guides: bool = True,
) -> Image.Image:
    """Create a back page with card backs mirrored for double-sided printing.

    Args:
        back_image: Card back image
        num_cards: Number of card backs to place (matches front page)
        draw_cut_guides: Whether to draw cut guide lines

    Returns:
        Letter-size page image at 300 DPI (horizontally mirrored for flip)
    """
    # Create white page
    page = Image.new("RGB", (LETTER_WIDTH_PX, LETTER_HEIGHT_PX), (255, 255, 255))
    draw = ImageDraw.Draw(page)

    # Calculate grid positioning (same as front page)
    grid_width = (COLS * SCALED_CARD_WIDTH) + ((COLS - 1) * GUTTER_PX)
    grid_height = (ROWS * SCALED_CARD_HEIGHT) + ((ROWS - 1) * GUTTER_PX)

    start_x = MARGIN_PX + (SAFE_WIDTH_PX - grid_width) // 2
    start_y = MARGIN_PX + (SAFE_HEIGHT_PX - grid_height) // 2

    # Scale the back image
    scaled_back = back_image.resize(
        (SCALED_CARD_WIDTH, SCALED_CARD_HEIGHT),
        Image.Resampling.LANCZOS
    )

    # Place backs in REVERSE column order for proper alignment when flipped
    # (columns go 2,1,0 instead of 0,1,2 for long-edge flip)
    for idx in range(min(num_cards, CARDS_PER_PAGE)):
        col = idx % COLS
        row = idx // COLS

        # Reverse the column for back side alignment
        mirrored_col = (COLS - 1) - col

        x = start_x + mirrored_col * (SCALED_CARD_WIDTH + GUTTER_PX)
        y = start_y + row * (SCALED_CARD_HEIGHT + GUTTER_PX)

        page.paste(scaled_back, (x, y))

    # Draw cut guides (same as front)
    if draw_cut_guides:
        guide_extend = 20

        for col in range(1, COLS):
            guide_x = start_x + col * SCALED_CARD_WIDTH + (col - 1) * GUTTER_PX + GUTTER_PX // 2
            for row in range(ROWS):
                y_start = start_y + row * (SCALED_CARD_HEIGHT + GUTTER_PX) - guide_extend
                y_end = start_y + row * (SCALED_CARD_HEIGHT + GUTTER_PX) + SCALED_CARD_HEIGHT + guide_extend
                draw.line([(guide_x, y_start), (guide_x, y_end)], fill=CUT_GUIDE_COLOR, width=1)

        for row in range(1, ROWS):
            guide_y = start_y + row * SCALED_CARD_HEIGHT + (row - 1) * GUTTER_PX + GUTTER_PX // 2
            for col in range(COLS):
                x_start = start_x + col * (SCALED_CARD_WIDTH + GUTTER_PX) - guide_extend
                x_end = start_x + col * (SCALED_CARD_WIDTH + GUTTER_PX) + SCALED_CARD_WIDTH + guide_extend
                draw.line([(x_start, guide_y), (x_end, guide_y)], fill=CUT_GUIDE_COLOR, width=1)

    return page


def create_print_page(
    cards: list[Image.Image],
    draw_cut_guides: bool = True,
) -> Image.Image:
    """Create a single print page with up to 9 cards.

    Args:
        cards: List of card images (up to 9)
        draw_cut_guides: Whether to draw cut guide lines

    Returns:
        Letter-size page image at 300 DPI
    """
    # Create white page
    page = Image.new("RGB", (LETTER_WIDTH_PX, LETTER_HEIGHT_PX), (255, 255, 255))
    draw = ImageDraw.Draw(page)

    # Calculate grid positioning to center cards in safe area
    grid_width = (COLS * SCALED_CARD_WIDTH) + ((COLS - 1) * GUTTER_PX)
    grid_height = (ROWS * SCALED_CARD_HEIGHT) + ((ROWS - 1) * GUTTER_PX)

    # Starting position (centered in safe area, offset by margin)
    start_x = MARGIN_PX + (SAFE_WIDTH_PX - grid_width) // 2
    start_y = MARGIN_PX + (SAFE_HEIGHT_PX - grid_height) // 2

    # Place cards in grid
    for idx, card in enumerate(cards):
        if idx >= CARDS_PER_PAGE:
            break

        col = idx % COLS
        row = idx // COLS

        x = start_x + col * (SCALED_CARD_WIDTH + GUTTER_PX)
        y = start_y + row * (SCALED_CARD_HEIGHT + GUTTER_PX)

        # Scale card to 93%
        scaled_card = card.resize(
            (SCALED_CARD_WIDTH, SCALED_CARD_HEIGHT),
            Image.Resampling.LANCZOS
        )

        page.paste(scaled_card, (x, y))

    # Draw cut guides
    if draw_cut_guides:
        guide_extend = 20  # How far guides extend into gutter

        # Vertical cut guides (between columns)
        for col in range(1, COLS):
            guide_x = start_x + col * SCALED_CARD_WIDTH + (col - 1) * GUTTER_PX + GUTTER_PX // 2
            # Draw for each row
            for row in range(ROWS):
                y_start = start_y + row * (SCALED_CARD_HEIGHT + GUTTER_PX) - guide_extend
                y_end = start_y + row * (SCALED_CARD_HEIGHT + GUTTER_PX) + SCALED_CARD_HEIGHT + guide_extend
                draw.line([(guide_x, y_start), (guide_x, y_end)], fill=CUT_GUIDE_COLOR, width=1)

        # Horizontal cut guides (between rows)
        for row in range(1, ROWS):
            guide_y = start_y + row * SCALED_CARD_HEIGHT + (row - 1) * GUTTER_PX + GUTTER_PX // 2
            # Draw for each column
            for col in range(COLS):
                x_start = start_x + col * (SCALED_CARD_WIDTH + GUTTER_PX) - guide_extend
                x_end = start_x + col * (SCALED_CARD_WIDTH + GUTTER_PX) + SCALED_CARD_WIDTH + guide_extend
                draw.line([(x_start, guide_y), (x_end, guide_y)], fill=CUT_GUIDE_COLOR, width=1)

    return page


def export_print_pdf(
    card_images: list[Path],
    output_path: Path,
    draw_cut_guides: bool = True,
    double_sided: bool = False,
    back_image_path: Optional[Path] = None,
) -> int:
    """Export cards to a multi-page print-ready PDF.

    Args:
        card_images: List of paths to card images
        output_path: Output PDF path
        draw_cut_guides: Whether to draw cut guides
        double_sided: If True, interleave back pages for duplex printing
        back_image_path: Path to card back image (required for double_sided)

    Returns:
        Number of pages created
    """
    if not card_images:
        logger.error("No card images to export")
        return 0

    # Load back image if double-sided
    back_image = None
    if double_sided:
        if not back_image_path or not back_image_path.exists():
            logger.error(f"Card back image required for double-sided printing: {back_image_path}")
            return 0
        back_image = Image.open(back_image_path)
        if back_image.mode != "RGB":
            back_image = back_image.convert("RGB")
        logger.info(f"Using card back: {back_image_path}")

    pages = []
    total_front_pages = (len(card_images) + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE

    mode_str = "double-sided" if double_sided else "single-sided"
    logger.info(f"Creating {total_front_pages} front pages for {len(card_images)} cards ({mode_str})...")

    for page_num in range(total_front_pages):
        start_idx = page_num * CARDS_PER_PAGE
        end_idx = min(start_idx + CARDS_PER_PAGE, len(card_images))

        # Load cards for this page
        page_cards = []
        for img_path in card_images[start_idx:end_idx]:
            try:
                img = Image.open(img_path)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                page_cards.append(img)
            except Exception as e:
                logger.error(f"Failed to load {img_path}: {e}")

        if page_cards:
            # Add front page
            front_page = create_print_page(page_cards, draw_cut_guides)
            pages.append(front_page)
            logger.info(f"  Front {page_num + 1}: cards {start_idx + 1}-{end_idx}")

            # Add back page if double-sided
            if double_sided and back_image:
                back_page = create_back_page(back_image, len(page_cards), draw_cut_guides)
                pages.append(back_page)
                logger.info(f"  Back {page_num + 1}: {len(page_cards)} card backs")

    # Save as PDF
    if pages:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pages[0].save(
            output_path,
            "PDF",
            resolution=DPI,
            save_all=True,
            append_images=pages[1:] if len(pages) > 1 else [],
        )
        logger.info(f"Saved PDF: {output_path}")

    return len(pages)


def find_lot_images(cards_dir: Path, limit: int = 0) -> list[Path]:
    """Find lot images in tgc_prep or outputs directories."""
    lot_images = []

    # Check for tgc_prep/lots structure
    tgc_prep = cards_dir / "tgc_prep" / "lots"
    if tgc_prep.exists():
        for batch_dir in sorted(tgc_prep.iterdir()):
            if batch_dir.is_dir() and batch_dir.name.startswith("batch_"):
                for img in sorted(batch_dir.glob("lot_*.png")):
                    lot_images.append(img)
        if lot_images:
            logger.info(f"Found {len(lot_images)} lots in tgc_prep")
            if limit > 0:
                lot_images = lot_images[:limit]
            return lot_images

    # Check sibling lots directory (series structure)
    lots_dir = cards_dir.parent / "lots"
    if not lots_dir.exists():
        # Try series/2026-Q1/lots as fallback
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        lots_dir = project_root / "series" / "2026-Q1" / "lots"

    if lots_dir.exists():
        for lot_dir in sorted(lots_dir.iterdir()):
            if not lot_dir.is_dir():
                continue
            if not lot_dir.name[0].isdigit():
                continue

            outputs_dir = lot_dir / "outputs"
            if outputs_dir.exists():
                for pattern in ["lot_1024x1536.png", "lot_*.png"]:
                    matches = list(outputs_dir.glob(pattern))
                    if matches:
                        lot_images.append(matches[0])
                        break

    if limit > 0:
        lot_images = lot_images[:limit]

    logger.info(f"Found {len(lot_images)} lots")
    return lot_images


def print_command(args: argparse.Namespace) -> int:
    """Execute the print export command."""
    cards_dir = args.cards_dir.resolve() if args.cards_dir else None
    project_root = Path(__file__).resolve().parent.parent.parent.parent

    if not cards_dir:
        cards_dir = project_root / "demo_cards"
        logger.info(f"No --cards-dir specified, using {cards_dir}")

    # Output directory
    output_dir = cards_dir / "playtest_prep"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find card back
    card_back_path = cards_dir / "tgc_prep" / "cards" / "back" / "card_back.png"
    if not card_back_path.exists():
        card_back_path = project_root / "templates" / "card_back.png"

    # Find lot back
    lot_back_path = cards_dir / "tgc_prep" / "lots" / "back" / "lot_back.png"
    if not lot_back_path.exists():
        lot_back_path = project_root / "templates" / "lots" / "Lot_Back.png"

    total_pages = 0
    results = []

    # Export card deck
    card_images = find_card_images(cards_dir, args.limit)
    if card_images:
        card_output = output_dir / "card_deck.pdf"
        num_pages = export_print_pdf(
            card_images,
            card_output,
            draw_cut_guides=not args.no_cut_guides,
            double_sided=True,
            back_image_path=card_back_path,
        )
        total_pages += num_pages
        results.append(f"Card deck: {len(card_images)} cards, {num_pages} pages -> {card_output.name}")

    # Export lot deck
    lot_images = find_lot_images(cards_dir, args.limit)
    if lot_images:
        lot_output = output_dir / "lot_deck.pdf"
        num_pages = export_print_pdf(
            lot_images,
            lot_output,
            draw_cut_guides=not args.no_cut_guides,
            double_sided=True,
            back_image_path=lot_back_path,
        )
        total_pages += num_pages
        results.append(f"Lot deck: {len(lot_images)} lots, {num_pages} pages -> {lot_output.name}")

    if not results:
        logger.error("No card or lot images found")
        return 1

    # Summary
    print()
    print("=== Print Export Complete ===")
    print(f"Output: {output_dir}")
    for r in results:
        print(f"  {r}")
    print(f"Total pages: {total_pages}")
    print()
    print("Office Depot Instructions:")
    print("  1. Upload PDFs to officedepot.com -> Print & Copy -> Copies")
    print("  2. Select: Cardstock (110 lb), Full color, Letter size")
    print("  3. Enable: Double-sided (flip on long edge)")
    print("  4. Choose same-day pickup")
    print(f"  Estimated cost: ${total_pages * 0.60:.2f}-${total_pages * 1.00:.2f}")

    return 0


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(
        description="Export Hypertext cards to print-ready PDF for Office Depot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m hypertext.tgc print --cards-dir demo_cards
  python -m hypertext.tgc print --cards-dir demo_cards --output playtest.pdf
  python -m hypertext.tgc print --cards-dir demo_cards --limit 18  # 3 pages
        """
    )

    parser.add_argument(
        "--cards-dir",
        type=Path,
        help="Directory containing card folders or tgc_prep",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output PDF path (default: <cards-dir>/exports/hypertext_print_sheets_letter_6up.pdf)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum cards to include (0 = all)",
    )
    parser.add_argument(
        "--no-cut-guides",
        action="store_true",
        help="Don't draw cut guide lines",
    )

    args = parser.parse_args()
    return print_command(args)


if __name__ == "__main__":
    exit(main())
