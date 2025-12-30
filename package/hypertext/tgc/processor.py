"""Image processor for TGC print preparation."""

import logging
from pathlib import Path
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# TGC Poker Card specifications (at 300 DPI)
PRINT_WIDTH = 825   # 2.5" + 0.25" bleed = 2.75" at 300 DPI
PRINT_HEIGHT = 1125  # 3.5" + 0.25" bleed = 3.75" at 300 DPI
BLEED_PX = 36       # 0.125" bleed on each side at 300 DPI
SAFE_WIDTH = PRINT_WIDTH - (2 * BLEED_PX)   # 753
SAFE_HEIGHT = PRINT_HEIGHT - (2 * BLEED_PX)  # 1053


class PrintProcessingError(Exception):
    """Error during print image processing."""
    pass


def validate_dimensions(image: Image.Image) -> bool:
    """Check if image has correct print dimensions.

    Args:
        image: PIL Image to validate

    Returns:
        True if dimensions are correct (825x1125)
    """
    return image.size == (PRINT_WIDTH, PRINT_HEIGHT)


def add_bleed(image: Image.Image, bleed_px: int = BLEED_PX) -> Image.Image:
    """Add bleed margins by extending edge pixels.

    Args:
        image: Source image (should be safe zone size: 753x1053)
        bleed_px: Bleed size in pixels (default 36)

    Returns:
        Image with bleed margins (825x1125)
    """
    w, h = image.size
    new_w = w + 2 * bleed_px
    new_h = h + 2 * bleed_px

    # Create new image with space for bleed
    result = Image.new("RGB", (new_w, new_h))

    # Paste original centered
    result.paste(image, (bleed_px, bleed_px))

    # Extend edges into bleed area
    # Top edge
    top_strip = image.crop((0, 0, w, 1))
    for y in range(bleed_px):
        result.paste(top_strip, (bleed_px, y))

    # Bottom edge
    bottom_strip = image.crop((0, h - 1, w, h))
    for y in range(new_h - bleed_px, new_h):
        result.paste(bottom_strip, (bleed_px, y))

    # Left edge (including corners from extended top/bottom)
    left_strip = result.crop((bleed_px, 0, bleed_px + 1, new_h))
    for x in range(bleed_px):
        result.paste(left_strip, (x, 0))

    # Right edge (including corners)
    right_strip = result.crop((new_w - bleed_px - 1, 0, new_w - bleed_px, new_h))
    for x in range(new_w - bleed_px, new_w):
        result.paste(right_strip, (x, 0))

    return result


def resize_to_safe_zone(
    image: Image.Image,
    fill_color: tuple = (30, 30, 30),
) -> Image.Image:
    """Resize image to fit safe zone, maintaining aspect ratio (letterbox).

    Args:
        image: Source image
        fill_color: Background color for letterboxing (default dark gray)

    Returns:
        Image resized to safe zone dimensions (753x1053)
    """
    # Calculate scale to fit in safe zone
    w, h = image.size
    scale_w = SAFE_WIDTH / w
    scale_h = SAFE_HEIGHT / h
    scale = min(scale_w, scale_h)

    # Resize maintaining aspect ratio
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Create safe zone canvas and center the image
    result = Image.new("RGB", (SAFE_WIDTH, SAFE_HEIGHT), fill_color)
    x = (SAFE_WIDTH - new_w) // 2
    y = (SAFE_HEIGHT - new_h) // 2
    result.paste(resized, (x, y))

    return result


def crop_to_fill(
    image: Image.Image,
    target_width: int,
    target_height: int,
) -> Image.Image:
    """Scale and center-crop image to fill target dimensions exactly.

    Scales up to cover the entire target area, then crops excess.
    No letterboxing - image fills the entire space.

    Args:
        image: Source image
        target_width: Target width in pixels
        target_height: Target height in pixels

    Returns:
        Image cropped to exact target dimensions
    """
    w, h = image.size

    # Calculate scale to FILL (cover) the target - use max, not min
    scale_w = target_width / w
    scale_h = target_height / h
    scale = max(scale_w, scale_h)

    # Resize to cover
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Center crop to target dimensions
    left = (new_w - target_width) // 2
    top = (new_h - target_height) // 2
    right = left + target_width
    bottom = top + target_height

    return resized.crop((left, top, right, bottom))


def prepare_for_print(
    image: Image.Image,
    mode: str = "resize",
    border: bool = True,
    border_percent: float = 0.10,
    border_color: tuple = (0, 0, 0),
) -> Image.Image:
    """Prepare image for TGC print.

    Args:
        image: Source card image (any size)
        mode: "resize" (scale to exact dimensions),
              "fill" (crop to fill), or "fit" (letterbox)
        border: If True, shrink image and add border for cut lines
        border_percent: Border size as percentage (0.10 = 10%)
        border_color: RGB tuple for border color (default black)

    Returns:
        Print-ready image (825x1125)
    """
    # Convert to RGB if needed
    if image.mode != "RGB":
        image = image.convert("RGB")

    if mode == "resize":
        # Direct resize to exact TGC dimensions
        resized = image.resize((PRINT_WIDTH, PRINT_HEIGHT), Image.Resampling.LANCZOS)
    elif mode == "fill":
        # Crop to fill - scales up and center-crops, no black bars
        resized = crop_to_fill(image, PRINT_WIDTH, PRINT_HEIGHT)
    else:
        # Fit with letterboxing
        safe_zone = resize_to_safe_zone(image)
        resized = add_bleed(safe_zone)

    # Add border if requested
    if border:
        # Calculate inner image size (shrunk by border_percent)
        inner_width = int(PRINT_WIDTH * (1 - border_percent))
        inner_height = int(PRINT_HEIGHT * (1 - border_percent))

        # Shrink the image
        shrunk = resized.resize((inner_width, inner_height), Image.Resampling.LANCZOS)

        # Create black canvas and center the shrunk image
        result = Image.new("RGB", (PRINT_WIDTH, PRINT_HEIGHT), border_color)
        x = (PRINT_WIDTH - inner_width) // 2
        y = (PRINT_HEIGHT - inner_height) // 2
        result.paste(shrunk, (x, y))
        return result

    return resized


def process_card_file(
    input_path: Path,
    output_path: Path,
    mode: str = "fill",
) -> None:
    """Process a card image file for print.

    Args:
        input_path: Source image path
        output_path: Destination path for print-ready image
        mode: "fill" (crop to fill) or "fit" (letterbox)
    """
    logger.info(f"Processing {input_path.name} for print...")

    image = Image.open(input_path)
    result = prepare_for_print(image, mode)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save as PNG for quality
    result.save(output_path, "PNG", optimize=True)

    logger.info(f"Saved print-ready image: {output_path} ({result.size[0]}x{result.size[1]})")


def process_card_back(
    input_path: Path,
    output_path: Path,
    mode: str = "fill",
) -> None:
    """Process card back image for print (same as card face processing).

    Args:
        input_path: Source card back image
        output_path: Destination path
        mode: "fill" (crop to fill) or "fit" (letterbox)
    """
    process_card_file(input_path, output_path, mode)
