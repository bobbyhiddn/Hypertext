"""The Game Crafter prep must never stretch or crop a 2:3 face."""
from PIL import Image

from hypertext.tgc.processor import (
    INNER_HEIGHT,
    INNER_WIDTH,
    PRINT_HEIGHT,
    PRINT_WIDTH,
    frame_fit,
    prepare_for_print,
)


def _face(color=(120, 60, 200)):
    image = Image.new("RGB", (1024, 1536), (40, 34, 70))
    inner = Image.new("RGB", (1000, 1512), color)
    image.paste(inner, (12, 12))
    return image


def test_frame_fit_is_exact_tgc_size_and_preserves_aspect():
    out = frame_fit(_face())
    assert out.size == (PRINT_WIDTH, PRINT_HEIGHT)
    # The face is scaled uniformly by the safe-zone height: 1536 -> 975, so
    # 1024 -> 650 wide; both bounds sit inside the true safe zone.
    scale = INNER_HEIGHT / 1536
    assert round(1024 * scale) == 650 and 650 <= INNER_WIDTH


def test_frame_fit_keeps_content_inside_safe_zone_and_mats_in_border_navy():
    out = frame_fit(_face())
    px = out.load()
    # Corners are the bleed mat, sampled from the face's own border navy.
    assert px[5, 5] == (40, 34, 70) and px[PRINT_WIDTH - 6, PRINT_HEIGHT - 6] == (40, 34, 70)
    # Safe-zone margin (75px = bleed 36 + 1/8" inside the cut) is mat on every side.
    for x, y in ((74, PRINT_HEIGHT // 2), (PRINT_WIDTH - 75, PRINT_HEIGHT // 2), (PRINT_WIDTH // 2, 74), (PRINT_WIDTH // 2, PRINT_HEIGHT - 75)):
        assert px[x, y] == (40, 34, 70)
    # The face interior color appears at the center, i.e. nothing was cropped or stretched away.
    assert px[PRINT_WIDTH // 2, PRINT_HEIGHT // 2] == (120, 60, 200)


def test_prepare_for_print_defaults_to_frame_fit_without_black_border():
    out = prepare_for_print(_face())
    assert out.size == (PRINT_WIDTH, PRINT_HEIGHT)
    assert out.load()[5, 5] == (40, 34, 70)
