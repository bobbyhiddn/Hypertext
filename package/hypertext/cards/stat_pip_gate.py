"""Template-relative visual acceptance for full-card stat pips.

The Gemini full-card workflow owns every visible pixel.  This module therefore
does not repair or redraw pips: it compares the generated raster with the exact
canonical type-by-rarity template and returns a deterministic accept/reject
report.  The template supplies the circle geometry, dark-outline luminance,
parchment luminance, and contrast used by every decision.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

from PIL import Image

CONTRACT = "hypertext.template-relative-stat-pip-gate/v1"
REFERENCE_SIZE = (1024, 1536)
ROW_NAMES = ("STAT_LORE", "STAT_CONTEXT", "STAT_COMPLEXITY")
Pixel = tuple[int, int, int]

# These are normalized slot anchors, not acceptance colors or drawn geometry.
# Every visual threshold and every circle-style decision is calibrated from the
# exact template supplied to ``inspect_stat_pips``.
_ROW_X = (
    (108, 160, 212, 264, 316),
    (414, 466, 518, 570, 622),
    (721, 773, 825, 877, 929),
)
_ROW_Y = 601

# Normalized radial sampling zones measured against the accepted v001 family.
# The template calibration below verifies that these zones really contain a
# bright empty interior, a dark circular outline, and bright exterior pixels.
_ZONES = {
    "core": (0.0, 7.0),
    "middle": (8.0, 15.0),
    "interior": (0.0, 15.0),
    "edge": (18.0, 23.0),
    "outside": (26.0, 29.0),
}


class StatPipGateError(ValueError):
    """The candidate or template cannot be evaluated by the visual contract."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _luma(pixel: Pixel) -> float:
    red, green, blue = pixel
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _percentile(values: Iterable[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise StatPipGateError("stat pip sampling zone is empty")
    position = fraction * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return float(ordered[lower])
    weight = position - lower
    return float(ordered[lower] * (1.0 - weight) + ordered[upper] * weight)


def _median(values: Iterable[float]) -> float:
    return _percentile(values, 0.5)


def _dark_fraction(values: Iterable[float], cutoff: float) -> float:
    samples = list(values)
    if not samples:
        raise StatPipGateError("stat pip sampling zone is empty")
    return sum(value <= cutoff for value in samples) / len(samples)


def _lumas(pixels: Iterable[Pixel]) -> list[float]:
    return [_luma(pixel) for pixel in pixels]


def _median_rgb(pixels: Iterable[Pixel]) -> tuple[float, float, float]:
    samples = list(pixels)
    if not samples:
        raise StatPipGateError("stat pip color sampling zone is empty")
    return tuple(_median(pixel[channel] for pixel in samples) for channel in range(3))


def _rgb_distance(
    first: tuple[float, float, float],
    second: tuple[float, float, float],
) -> float:
    return math.sqrt(sum((left - right) ** 2 for left, right in zip(first, second)))


def _image_scale(image: Image.Image) -> tuple[float, float, float]:
    sx = image.width / REFERENCE_SIZE[0]
    sy = image.height / REFERENCE_SIZE[1]
    return sx, sy, min(sx, sy)


def _slot_zones(
    image: Image.Image,
    *,
    base_x: int,
) -> dict[str, list[Pixel]]:
    """Return normalized radial RGB samples for one template slot."""
    sx, sy, radius_scale = _image_scale(image)
    center_x = round(base_x * sx)
    center_y = round(_ROW_Y * sy)
    maximum = math.ceil(_ZONES["outside"][1] * radius_scale) + 2
    pixels = image.load()
    zones = {name: [] for name in _ZONES}

    for y in range(max(0, center_y - maximum), min(image.height, center_y + maximum + 1)):
        for x in range(max(0, center_x - maximum), min(image.width, center_x + maximum + 1)):
            radius = math.hypot(x - center_x, y - center_y) / radius_scale
            pixel = pixels[x, y]
            for name, (inner, outer) in _ZONES.items():
                if inner <= radius <= outer:
                    zones[name].append(pixel)
    return zones


def _all_slot_zones(image: Image.Image) -> list[tuple[str, int, dict[str, list[Pixel]]]]:
    return [
        (row_name, slot + 1, _slot_zones(image, base_x=base_x))
        for row_name, row in zip(ROW_NAMES, _ROW_X, strict=True)
        for slot, base_x in enumerate(row)
    ]


def _calibrate_template(template: Image.Image) -> dict[str, float]:
    """Derive the accepted empty-circle palette and geometry from a template."""
    samples = _all_slot_zones(template)
    interior_pixels = [
        pixel for _, _, zones in samples for pixel in zones["interior"]
    ]
    edge_pixels = [pixel for _, _, zones in samples for pixel in zones["edge"]]
    outside_pixels = [
        pixel for _, _, zones in samples for pixel in zones["outside"]
    ]
    interior = _lumas(interior_pixels)
    edge = _lumas(edge_pixels)
    outside = _lumas(outside_pixels)

    interior_luma = _median(interior)
    outline_luma = _median(edge)
    outside_luma = _median(outside)
    contrast = interior_luma - outline_luma
    if contrast < 75.0:
        raise StatPipGateError(
            "template stat pips do not expose the required dark-outline/empty-interior contrast"
        )

    dark_cutoff = outline_luma + contrast * 0.5
    outline_dark_fraction = _dark_fraction(edge, dark_cutoff)
    interior_dark_fraction = _dark_fraction(interior, dark_cutoff)
    outside_dark_fraction = _dark_fraction(outside, dark_cutoff)
    if outline_dark_fraction < 0.65:
        raise StatPipGateError("template stat pip outline is not a continuous dark circle")
    if interior_dark_fraction > 0.10:
        raise StatPipGateError("template stat pip interior is not visibly empty")
    if outside_dark_fraction > 0.15:
        raise StatPipGateError("template stat pip geometry is not isolated from its exterior")

    # The dark body of the accepted outline is also the required filled-pip
    # palette. Restricting calibration to its darkest pixels excludes
    # anti-aliasing and makes wrong-hue dark fills fail independently of luma.
    palette_cutoff = outline_luma + contrast * 0.18
    outline_palette = [
        pixel for pixel in edge_pixels if _luma(pixel) <= palette_cutoff
    ]
    if len(outline_palette) < len(edge_pixels) * 0.25:
        raise StatPipGateError("template stat pip outline has no stable dark palette")
    outline_rgb = _median_rgb(outline_palette)
    outline_color_distance_p90 = _percentile(
        (_rgb_distance(pixel, outline_rgb) for pixel in outline_palette),
        0.90,
    )

    return {
        "interior_luma": interior_luma,
        "outline_luma": outline_luma,
        "outside_luma": outside_luma,
        "contrast": contrast,
        "dark_cutoff": dark_cutoff,
        "outline_dark_fraction": outline_dark_fraction,
        "interior_dark_fraction": interior_dark_fraction,
        "outside_dark_fraction": outside_dark_fraction,
        "palette_cutoff": palette_cutoff,
        "outline_red": outline_rgb[0],
        "outline_green": outline_rgb[1],
        "outline_blue": outline_rgb[2],
        "outline_color_distance_p90": outline_color_distance_p90,
    }


def _slot_metrics(
    zones: dict[str, list[Pixel]],
    calibration: dict[str, float],
) -> dict[str, float]:
    cutoff = calibration["dark_cutoff"]
    palette_cutoff = calibration["palette_cutoff"]
    outline_rgb = (
        calibration["outline_red"],
        calibration["outline_green"],
        calibration["outline_blue"],
    )
    metrics: dict[str, float] = {}
    for name in _ZONES:
        lumas = _lumas(zones[name])
        palette_pixels = [
            pixel for pixel, value in zip(zones[name], lumas, strict=True)
            if value <= palette_cutoff
        ]
        metrics[f"{name}_median_luma"] = _median(lumas)
        metrics[f"{name}_dark_fraction"] = _dark_fraction(lumas, cutoff)
        metrics[f"{name}_palette_rgb_distance"] = (
            _rgb_distance(_median_rgb(palette_pixels), outline_rgb)
            if palette_pixels
            else math.sqrt(3 * 255**2)
        )
    interior_lumas = _lumas(zones["interior"])
    metrics["interior_luma_p10"] = _percentile(interior_lumas, 0.10)
    metrics["interior_luma_p90"] = _percentile(interior_lumas, 0.90)
    metrics["interior_luma_spread"] = (
        metrics["interior_luma_p90"] - metrics["interior_luma_p10"]
    )
    metrics["core_middle_luma_step"] = abs(
        metrics["middle_median_luma"] - metrics["core_median_luma"]
    )
    metrics["empty_outline_contrast"] = (
        metrics["interior_median_luma"] - metrics["edge_median_luma"]
    )
    return metrics


def _maximum_color_distance(calibration: dict[str, float]) -> float:
    # Accepted templates contain parchment texture near the anti-aliased edge,
    # so their measured dispersion can only widen the palette tolerance within
    # a bounded RGB distance. The reference color itself remains template-owned.
    return min(
        56.0,
        max(48.0, calibration["outline_color_distance_p90"] * 1.8),
    )


def _filled_defects(metrics: dict[str, float], calibration: dict[str, float]) -> list[str]:
    defects: list[str] = []
    if metrics["core_dark_fraction"] < 0.90:
        defects.append("filled-center-not-dark")
    if (
        metrics["interior_dark_fraction"] < 0.82
        or metrics["middle_dark_fraction"] < 0.75
    ):
        defects.append("filled-interior-not-solid")

    maximum_spread = max(24.0, calibration["contrast"] * 0.30)
    maximum_radial_step = max(16.0, calibration["contrast"] * 0.22)
    if (
        metrics["interior_luma_spread"] > maximum_spread
        or metrics["core_middle_luma_step"] > maximum_radial_step
    ):
        defects.append("filled-concentric-or-nonuniform")

    maximum_color_distance = _maximum_color_distance(calibration)
    if (
        metrics["core_palette_rgb_distance"] > maximum_color_distance
        or metrics["middle_palette_rgb_distance"] > maximum_color_distance
    ):
        defects.append("filled-fill-style-mismatch")

    minimum_edge = max(0.28, calibration["outline_dark_fraction"] * 0.30)
    maximum_outside = max(0.20, calibration["outside_dark_fraction"] + 0.15)
    if (
        metrics["edge_dark_fraction"] < minimum_edge
        or metrics["outside_dark_fraction"] > maximum_outside
    ):
        defects.append("filled-geometry-mismatch")
    return defects


def _empty_defects(metrics: dict[str, float], calibration: dict[str, float]) -> list[str]:
    defects: list[str] = []
    if (
        metrics["core_dark_fraction"] > 0.15
        or metrics["interior_dark_fraction"] > 0.20
    ):
        defects.append("empty-interior-not-empty")

    minimum_edge = max(0.32, calibration["outline_dark_fraction"] * 0.38)
    minimum_contrast = calibration["contrast"] * 0.36
    maximum_outline_luma = (
        calibration["interior_luma"] - calibration["contrast"] * 0.35
    )
    if (
        metrics["edge_dark_fraction"] < minimum_edge
        or metrics["empty_outline_contrast"] < minimum_contrast
        or metrics["edge_median_luma"] > maximum_outline_luma
        or metrics["edge_palette_rgb_distance"]
        > _maximum_color_distance(calibration)
    ):
        defects.append("empty-outline-style-mismatch")

    maximum_outside = max(0.25, calibration["outside_dark_fraction"] + 0.20)
    if metrics["outside_dark_fraction"] > maximum_outside:
        defects.append("empty-geometry-mismatch")
    return defects


def _expected_counts(values: Iterable[Any]) -> tuple[int, int, int]:
    try:
        counts = tuple(int(value) for value in values)
    except (TypeError, ValueError) as exc:
        raise StatPipGateError("stat pip counts must be integers") from exc
    if len(counts) != 3 or any(value < 0 or value > 5 for value in counts):
        raise StatPipGateError(f"stat pip counts must contain three values within 0..5: {counts}")
    return counts  # type: ignore[return-value]


def inspect_stat_pips(
    candidate_path: str | Path,
    template_path: str | Path,
    expected_counts: Iterable[Any],
) -> dict[str, Any]:
    """Inspect all 15 pips and return a deterministic JSON-serializable report."""
    candidate_path = Path(candidate_path)
    template_path = Path(template_path)
    counts = _expected_counts(expected_counts)
    if not candidate_path.is_file():
        raise StatPipGateError(f"candidate image is missing: {candidate_path}")
    if not template_path.is_file():
        raise StatPipGateError(f"template image is missing: {template_path}")

    try:
        with Image.open(candidate_path) as source:
            candidate = source.convert("RGB")
        with Image.open(template_path) as source:
            template = source.convert("RGB")
    except (OSError, ValueError) as exc:
        raise StatPipGateError(f"stat pip image decode failed: {exc}") from exc

    candidate_ratio = candidate.width / candidate.height
    template_ratio = template.width / template.height
    reference_ratio = REFERENCE_SIZE[0] / REFERENCE_SIZE[1]
    if abs(candidate_ratio - reference_ratio) > 0.01:
        raise StatPipGateError(
            f"candidate does not use the full-card 2:3 contract: {candidate.size}"
        )
    if abs(template_ratio - reference_ratio) > 0.01:
        raise StatPipGateError(
            f"template does not use the canonical full-card layout: {template.size}"
        )

    calibration = _calibrate_template(template)
    rows: list[dict[str, Any]] = []
    defects: list[dict[str, Any]] = []
    observed_counts: list[int] = []
    slot_samples = _all_slot_zones(candidate)
    sample_index = 0

    for row_name, expected_count in zip(ROW_NAMES, counts, strict=True):
        row_slots: list[dict[str, Any]] = []
        observed_count = 0
        for slot in range(1, 6):
            sampled_row, sampled_slot, zones = slot_samples[sample_index]
            sample_index += 1
            if (sampled_row, sampled_slot) != (row_name, slot):
                raise AssertionError("internal stat pip slot ordering drift")
            expected_state = "filled" if slot <= expected_count else "empty"
            metrics = _slot_metrics(zones, calibration)
            observed_state = (
                "filled" if metrics["core_dark_fraction"] >= 0.65 else "empty"
            )
            if observed_state == "filled":
                observed_count += 1
            slot_defects = (
                _filled_defects(metrics, calibration)
                if expected_state == "filled"
                else _empty_defects(metrics, calibration)
            )
            slot_record = {
                "slot": slot,
                "expected_state": expected_state,
                "observed_state": observed_state,
                "passed": not slot_defects,
                "defects": slot_defects,
                "metrics": {name: round(value, 4) for name, value in metrics.items()},
            }
            row_slots.append(slot_record)
            for code in slot_defects:
                defects.append({"code": code, "row": row_name, "slot": slot})
        observed_counts.append(observed_count)
        rows.append(
            {
                "name": row_name,
                "expected_count": expected_count,
                "observed_count": observed_count,
                "passed": all(slot["passed"] for slot in row_slots),
                "slots": row_slots,
            }
        )

    report = {
        "contract": CONTRACT,
        "passed": not defects and tuple(observed_counts) == counts,
        "candidate": {
            "path": str(candidate_path),
            "sha256": _sha256(candidate_path),
            "dimensions": list(candidate.size),
        },
        "template": {
            "path": str(template_path),
            "sha256": _sha256(template_path),
            "dimensions": list(template.size),
        },
        "expected_counts": dict(zip(ROW_NAMES, counts, strict=True)),
        "observed_counts": dict(zip(ROW_NAMES, observed_counts, strict=True)),
        "calibration": {
            name: round(value, 4) for name, value in calibration.items()
        },
        "rows": rows,
        "defects": defects,
    }
    return report


def write_report(report: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def inspect_card_stat_pips(
    card_dir: str | Path,
    *,
    candidate_path: str | Path | None = None,
    template_path: str | Path | None = None,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Resolve a card's canonical template and inspect its generated full face."""
    card_dir = Path(card_dir)
    card_path = card_dir / "card.json"
    try:
        card = json.loads(card_path.read_text(encoding="utf-8"))
        content = card["content"]
        card_type = str(content["CARD_TYPE"]).upper()
        rarity = str(content["RARITY_TEXT"]).upper()
        counts = tuple(content[name] for name in ROW_NAMES)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise StatPipGateError(f"invalid card record for stat pip gate: {card_path}") from exc

    template_record: dict[str, Any] | None = None
    if template_path is None:
        from hypertext.cards.template_matrix import resolve_template_record

        template_record = resolve_template_record(card_type, rarity, verify=True)
        template_path = template_record["path"]
    candidate_path = candidate_path or card_dir / "outputs" / "card_1024x1536.png"
    report = inspect_stat_pips(candidate_path, template_path, counts)
    report["target"] = {"card_type": card_type, "rarity": rarity}
    report["card_record"] = {
        "path": str(card_path),
        "sha256": _sha256(card_path),
    }
    if template_record is not None:
        report["template"].update(
            {
                "repository_path": template_record["repo_path"],
                "manifest_path": str(template_record["manifest_path"]),
                "manifest_sha256": template_record["manifest_sha256"],
                "manifest_schema_version": template_record["manifest_schema_version"],
                "manifest_status": template_record["manifest_status"],
                "template_version": template_record["template_version"],
            }
        )
    if report_path is not None:
        write_report(report, report_path)
    return report


def defect_summary(report: dict[str, Any]) -> str:
    defects = report.get("defects", [])
    if not defects:
        return "no stat pip defects"
    return "; ".join(
        f"{item['row']}[{item['slot']}]={item['code']}" for item in defects
    )
