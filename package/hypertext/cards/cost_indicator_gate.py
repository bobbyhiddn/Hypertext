"""Template-relative acceptance for the printed Word Card activation cost.

The visible face remains a complete Gemini output.  This module never paints,
repairs, or reconstructs the cost indicator.  It verifies the structured rarity
contract, derives the accepted visible arrangement from the exact canonical
type-by-rarity template, and rejects the generated full-resolution raster when
the plus sign or plain card-back glyphs differ from that arrangement.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

from PIL import Image

from hypertext.cards.visual_descriptors import load_descriptors

CONTRACT = "hypertext.template-relative-cost-indicator-gate/v1"
REFERENCE_SIZE = (1024, 1536)
CARD_GLYPH = "\U0001f0a0"

# The manifest's rarity edit envelope is [650, 10, 838, 162] on its
# 848x1264 evidence canvas.  This normalized subregion excludes the rarity
# badge while retaining every canonical cost glyph and bounded placement.
_COST_REGION = (790, 80, 1002, 194)
_RARITIES = ("COMMON", "UNCOMMON", "RARE", "GLORIOUS")

Pixel = tuple[int, int, int]
Box = tuple[int, int, int, int]


class CostIndicatorGateError(ValueError):
    """The candidate, recipe, or canonical template cannot be evaluated."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _luma(pixel: Pixel) -> float:
    red, green, blue = pixel
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _percentile(values: Iterable[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise CostIndicatorGateError("cost indicator sampling zone is empty")
    position = fraction * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return float(ordered[lower])
    weight = position - lower
    return float(ordered[lower] * (1.0 - weight) + ordered[upper] * weight)


def _scale_box(image: Image.Image, box: Box) -> Box:
    sx = image.width / REFERENCE_SIZE[0]
    sy = image.height / REFERENCE_SIZE[1]
    left, top, right, bottom = box
    return (
        max(0, round(left * sx)),
        max(0, round(top * sy)),
        min(image.width, round(right * sx)),
        min(image.height, round(bottom * sy)),
    )


def _reference_box(image: Image.Image, box: Box) -> Box:
    sx = REFERENCE_SIZE[0] / image.width
    sy = REFERENCE_SIZE[1] / image.height
    return tuple(
        round(value * (sx if index % 2 == 0 else sy))
        for index, value in enumerate(box)
    )  # type: ignore[return-value]


def _dark_mask(image: Image.Image, cutoff: float) -> list[list[bool]]:
    pixels = image.load()
    return [
        [_luma(pixels[x, y]) <= cutoff for x in range(image.width)]
        for y in range(image.height)
    ]


def _close_bands(bands: list[tuple[int, int]], maximum_gap: int) -> list[tuple[int, int]]:
    if not bands:
        return []
    merged = [bands[0]]
    for left, right in bands[1:]:
        previous_left, previous_right = merged[-1]
        if left - previous_right <= maximum_gap:
            merged[-1] = (previous_left, right)
        else:
            merged.append((left, right))
    return merged


def _projection_bands(mask: list[list[bool]], *, image_scale: float) -> list[tuple[int, int]]:
    if not mask or not mask[0]:
        return []
    height, width = len(mask), len(mask[0])
    minimum_column_ink = max(3, round(4 * image_scale))
    active = [
        sum(mask[y][x] for y in range(height)) >= minimum_column_ink
        for x in range(width)
    ]
    raw: list[tuple[int, int]] = []
    start: int | None = None
    for x, is_active in enumerate(active + [False]):
        if is_active and start is None:
            start = x
        elif not is_active and start is not None:
            raw.append((start, x))
            start = None
    return _close_bands(raw, max(2, round(3 * image_scale)))


def _cross_score(mask: list[list[bool]], box: Box) -> dict[str, float]:
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    rows = [sum(mask[y][x] for x in range(left, right)) for y in range(top, bottom)]
    columns = [sum(mask[y][x] for y in range(top, bottom)) for x in range(left, right)]
    return {
        "horizontal_coverage": max(rows, default=0) / max(width, 1),
        "vertical_coverage": max(columns, default=0) / max(height, 1),
    }


def _feature_records(
    image: Image.Image,
    *,
    dark_cutoff: float,
) -> tuple[list[dict[str, Any]], Box]:
    region = _scale_box(image, _COST_REGION)
    crop = image.crop(region).convert("RGB")
    mask = _dark_mask(crop, dark_cutoff)
    scale = min(image.width / REFERENCE_SIZE[0], image.height / REFERENCE_SIZE[1])
    records: list[dict[str, Any]] = []

    for left, right in _projection_bands(mask, image_scale=scale):
        points = [
            (x, y)
            for y in range(crop.height)
            for x in range(left, right)
            if mask[y][x]
        ]
        if not points:
            continue
        top = min(y for _, y in points)
        bottom = max(y for _, y in points) + 1
        box = (left, top, right, bottom)
        reference = _reference_box(
            image,
            (
                region[0] + left,
                region[1] + top,
                region[0] + right,
                region[1] + bottom,
            ),
        )
        width = reference[2] - reference[0]
        height = reference[3] - reference[1]
        center_y = (reference[1] + reference[3]) / 2
        # Generated gloss copy can extend beneath the cost treatment on long
        # cards.  The canonical template pins every cost glyph's center to the
        # upper-right header band; lower text is outside the indicator even
        # though it can intersect the broad manifest rarity envelope.
        if not 90 <= center_y <= 160:
            continue
        area = len(points) / max(scale**2, 1e-9)
        cross = _cross_score(mask, box)
        if width >= 28 and height >= 46 and area >= 260:
            kind = "card"
        elif (
            10 <= width <= 38
            and 14 <= height <= 44
            and area >= 45
            and min(cross.values()) >= 0.50
        ):
            kind = "plus"
        elif width >= 7 and height >= 7 and area >= 40:
            kind = "unknown"
        else:
            continue
        records.append(
            {
                "kind": kind,
                "box": list(reference),
                "center": [
                    round((reference[0] + reference[2]) / 2, 3),
                    round((reference[1] + reference[3]) / 2, 3),
                ],
                "width": width,
                "height": height,
                "ink_area": round(area, 3),
                "cross": {name: round(value, 4) for name, value in cross.items()},
                "native_box": box,
            }
        )
    records.sort(key=lambda item: item["center"][0])
    return records, region


def _card_face_metrics(
    image: Image.Image,
    feature: dict[str, Any],
    *,
    dark_cutoff: float,
) -> dict[str, float]:
    left, top, right, bottom = feature["box"]
    sx = image.width / REFERENCE_SIZE[0]
    sy = image.height / REFERENCE_SIZE[1]
    left, right = round(left * sx), round(right * sx)
    top, bottom = round(top * sy), round(bottom * sy)
    width, height = right - left, bottom - top

    # The foreground card is the leftmost of the slightly offset stack.  This
    # inset samples only its navy face, excluding its gold/navy outline.  A
    # diamond, word, number, or other label inside that face becomes a bounded
    # connected bright region and is therefore rejected.
    sample_box = (
        left + round(width * 0.22),
        top + round(height * 0.20),
        left + round(width * 0.68),
        top + round(height * 0.72),
    )
    sample = image.crop(sample_box).convert("RGB")
    pixel_reader = getattr(sample, "get_flattened_data", sample.getdata)
    pixels = list(pixel_reader())
    lumas = [_luma(pixel) for pixel in pixels]
    bright_cutoff = max(125.0, dark_cutoff + 25.0)
    bright = [value > bright_cutoff for value in lumas]
    return {
        "dark_fraction": sum(value <= dark_cutoff for value in lumas) / len(lumas),
        "bright_fraction": sum(bright) / len(bright),
        "luma_p10": _percentile(lumas, 0.10),
        "luma_p90": _percentile(lumas, 0.90),
        "luma_spread": _percentile(lumas, 0.90) - _percentile(lumas, 0.10),
    }


def _expected_display(card_bonus: int) -> str | None:
    return None if card_bonus == 0 else "+" + CARD_GLYPH * card_bonus


def _recipe_expectation(card: dict[str, Any]) -> tuple[str, str, int, list[dict[str, Any]]]:
    try:
        content = card["content"]
        card_type = str(content["CARD_TYPE"]).upper()
        rarity = str(content["RARITY_TEXT"]).upper()
        rarity_icon = str(content["RARITY_ICON"]).upper()
    except (KeyError, TypeError, ValueError) as exc:
        raise CostIndicatorGateError("card recipe lacks canonical type/rarity content") from exc

    descriptors = load_descriptors()
    if rarity not in descriptors["rarities"]:
        raise CostIndicatorGateError(f"unsupported cost-indicator rarity: {rarity}")
    if card_type not in descriptors["types"]:
        raise CostIndicatorGateError(f"unsupported cost-indicator card type: {card_type}")
    defects: list[dict[str, Any]] = []
    if rarity_icon != rarity:
        defects.append(
            {
                "code": "cost-recipe-rarity-mismatch",
                "detail": f"RARITY_ICON={rarity_icon!r} does not match RARITY_TEXT={rarity!r}",
            }
        )

    card_bonus = int(descriptors["rarities"][rarity]["card_bonus"])
    try:
        indicator = card["style_guide"]["iconography"]["cost_indicator"]
        placement = indicator["placement"]
        costs = indicator["costs"]
    except (KeyError, TypeError) as exc:
        raise CostIndicatorGateError(
            "card recipe lacks style_guide.iconography.cost_indicator"
        ) from exc

    if placement != "below_rarity":
        defects.append(
            {
                "code": "cost-recipe-placement-mismatch",
                "detail": f"cost placement must be 'below_rarity', got {placement!r}",
            }
        )
    for declared_rarity in _RARITIES:
        declared_bonus = int(descriptors["rarities"][declared_rarity]["card_bonus"])
        expected = _expected_display(declared_bonus)
        try:
            entry = costs[declared_rarity]
            actual = None if entry is None else entry["display"]
        except (KeyError, TypeError):
            actual = "__MISSING__"
        if actual != expected:
            defects.append(
                {
                    "code": "cost-recipe-value-mismatch",
                    "rarity": declared_rarity,
                    "expected": expected,
                    "actual": actual,
                }
            )
    return card_type, rarity, card_bonus, defects


def _kind_counts(features: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts = {"plus": 0, "card": 0, "unknown": 0}
    for feature in features:
        counts[feature["kind"]] += 1
    return counts


def _placement_defects(
    template_features: list[dict[str, Any]],
    candidate_features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    defects: list[dict[str, Any]] = []
    template_known = [item for item in template_features if item["kind"] != "unknown"]
    candidate_known = [item for item in candidate_features if item["kind"] != "unknown"]
    if [item["kind"] for item in candidate_known] != [item["kind"] for item in template_known]:
        defects.append(
            {
                "code": "cost-indicator-order-or-duplication-mismatch",
                "expected_order": [item["kind"] for item in template_known],
                "observed_order": [item["kind"] for item in candidate_known],
            }
        )
        return defects
    if not template_known:
        return defects

    x_offsets = [
        candidate["center"][0] - template["center"][0]
        for template, candidate in zip(template_known, candidate_known, strict=True)
    ]
    y_offsets = [
        candidate["center"][1] - template["center"][1]
        for template, candidate in zip(template_known, candidate_known, strict=True)
    ]
    median_x = _percentile(x_offsets, 0.5)
    median_y = _percentile(y_offsets, 0.5)
    residual = max(
        [abs(value - median_x) for value in x_offsets]
        + [abs(value - median_y) for value in y_offsets]
    )
    if abs(median_x) > 30 or abs(median_y) > 20 or residual > 13:
        defects.append(
            {
                "code": "cost-indicator-placement-mismatch",
                "translation": [round(median_x, 3), round(median_y, 3)],
                "maximum_relative_residual": round(residual, 3),
            }
        )

    for index, (template, candidate) in enumerate(
        zip(template_known, candidate_known, strict=True), start=1
    ):
        width_ratio = candidate["width"] / max(template["width"], 1)
        height_ratio = candidate["height"] / max(template["height"], 1)
        if not (0.62 <= width_ratio <= 1.48 and 0.62 <= height_ratio <= 1.48):
            defects.append(
                {
                    "code": "cost-indicator-geometry-mismatch",
                    "feature": index,
                    "kind": candidate["kind"],
                    "size_ratio": [round(width_ratio, 3), round(height_ratio, 3)],
                }
            )
    return defects


def inspect_cost_indicator(
    candidate_path: str | Path,
    template_path: str | Path,
    card: dict[str, Any],
    *,
    expected_template_sha256: str | None = None,
    dark_cutoff: float = 120.0,
) -> dict[str, Any]:
    """Compare one generated cost indicator with its recipe and template."""
    candidate_path = Path(candidate_path)
    template_path = Path(template_path)
    if not candidate_path.is_file():
        raise CostIndicatorGateError(f"candidate image is missing: {candidate_path}")
    if not template_path.is_file():
        raise CostIndicatorGateError(f"template image is missing: {template_path}")
    template_digest = _sha256(template_path)
    if expected_template_sha256 and template_digest != expected_template_sha256:
        raise CostIndicatorGateError(
            "cost indicator template failed the manifest SHA-256 check"
        )

    try:
        with Image.open(candidate_path) as source:
            candidate = source.convert("RGB")
        with Image.open(template_path) as source:
            template = source.convert("RGB")
    except (OSError, ValueError) as exc:
        raise CostIndicatorGateError(f"cost indicator image decode failed: {exc}") from exc
    if candidate.size != REFERENCE_SIZE:
        raise CostIndicatorGateError(
            f"candidate must be the full-resolution 1024x1536 card: {candidate.size}"
        )
    reference_ratio = REFERENCE_SIZE[0] / REFERENCE_SIZE[1]
    if abs(template.width / template.height - reference_ratio) > 0.01:
        raise CostIndicatorGateError(
            f"template does not use the canonical full-card layout: {template.size}"
        )

    card_type, rarity, expected_cards, defects = _recipe_expectation(card)
    template_features, _ = _feature_records(template, dark_cutoff=dark_cutoff)
    candidate_features, _ = _feature_records(candidate, dark_cutoff=dark_cutoff)
    template_counts = _kind_counts(template_features)
    observed_counts = _kind_counts(candidate_features)

    expected_plus = 1 if expected_cards else 0
    if template_counts != {"plus": expected_plus, "card": expected_cards, "unknown": 0}:
        raise CostIndicatorGateError(
            "hash-verified template cost treatment disagrees with the structured rarity descriptor: "
            f"rarity={rarity}, expected plus/cards={expected_plus}/{expected_cards}, "
            f"template={template_counts}"
        )

    if observed_counts["unknown"]:
        defects.append(
            {
                "code": "cost-indicator-malformed-or-extra",
                "count": observed_counts["unknown"],
            }
        )
    if observed_counts["plus"] != expected_plus:
        defects.append(
            {
                "code": "cost-plus-sign-count-mismatch",
                "expected": expected_plus,
                "observed": observed_counts["plus"],
            }
        )
    if observed_counts["card"] != expected_cards:
        defects.append(
            {
                "code": "cost-card-count-mismatch",
                "expected": expected_cards,
                "observed": observed_counts["card"],
            }
        )
    if expected_cards and observed_counts["plus"] == expected_plus:
        template_plus = next(item for item in template_features if item["kind"] == "plus")
        candidate_plus = next(item for item in candidate_features if item["kind"] == "plus")
        minimum_cross = min(template_plus["cross"].values()) * 0.72
        if min(candidate_plus["cross"].values()) < max(0.48, minimum_cross):
            defects.append(
                {
                    "code": "cost-plus-sign-malformed",
                    "metrics": candidate_plus["cross"],
                }
            )

    if (
        observed_counts["unknown"] == 0
        and observed_counts["plus"] == expected_plus
        and observed_counts["card"] == expected_cards
    ):
        defects.extend(_placement_defects(template_features, candidate_features))

        template_cards = [item for item in template_features if item["kind"] == "card"]
        candidate_cards = [item for item in candidate_features if item["kind"] == "card"]
        for index, (expected, observed) in enumerate(
            zip(template_cards, candidate_cards, strict=True), start=1
        ):
            template_metrics = _card_face_metrics(
                template, expected, dark_cutoff=dark_cutoff
            )
            candidate_metrics = _card_face_metrics(
                candidate, observed, dark_cutoff=dark_cutoff
            )
            maximum_bright = max(0.045, template_metrics["bright_fraction"] + 0.035)
            maximum_p90 = max(112.0, template_metrics["luma_p90"] + 42.0)
            if (
                candidate_metrics["bright_fraction"] > maximum_bright
                or candidate_metrics["luma_p90"] > maximum_p90
            ):
                defects.append(
                    {
                        "code": "cost-card-label-or-face-mismatch",
                        "card": index,
                        "metrics": {
                            name: round(value, 4)
                            for name, value in candidate_metrics.items()
                        },
                        "template_metrics": {
                            name: round(value, 4)
                            for name, value in template_metrics.items()
                        },
                    }
                )

    return {
        "contract": CONTRACT,
        "passed": not defects,
        "target": {
            "card_type": card_type,
            "rarity": rarity,
            "expected_card_count": expected_cards,
            "expected_plus_count": expected_plus,
            "placement": "below_rarity",
        },
        "candidate": {
            "path": str(candidate_path),
            "sha256": _sha256(candidate_path),
            "dimensions": list(candidate.size),
        },
        "template": {
            "path": str(template_path),
            "sha256": template_digest,
            "dimensions": list(template.size),
        },
        "recipe": {
            "canonical_sha256": _canonical_sha256(card),
            "declared_display": _expected_display(expected_cards),
        },
        "region": list(_COST_REGION),
        "template_features": [
            {key: value for key, value in item.items() if key != "native_box"}
            for item in template_features
        ],
        "candidate_features": [
            {key: value for key, value in item.items() if key != "native_box"}
            for item in candidate_features
        ],
        "observed": observed_counts,
        "defects": defects,
    }
