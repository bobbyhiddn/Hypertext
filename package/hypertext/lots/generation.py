#!/usr/bin/env python3
"""
Lot (Phase Card) Generation Pipeline for Hypertext.

Phase names and compositions are universal (loaded from templates/phases.yml).
Only flavor text and context vary per series (stored in series/X/lots/lot_content.yml).

Phases:
  - init: Create lot_content.yml template for a series
  - generate: Generate context/flavor via Gemini for series theme
  - render: Render all 30 phase card PNGs
  - rebuild: Force re-render all with grading and retry loop
  - batch: Full pipeline (generate + render)
  - export: Package cards for playtest/print platforms
  - grade: Evaluate rendered lot cards against quality rubric

Usage:
  python -m hypertext.lots.generation --phase init --series series/2026-Q1
  python -m hypertext.lots.generation --phase generate --series series/2026-Q1
  python -m hypertext.lots.generation --phase render --series series/2026-Q1 --parallel 4
  python -m hypertext.lots.generation --phase rebuild --series series/2026-Q1 --parallel 2
  python -m hypertext.lots.generation --phase batch --series series/2026-Q1
  python -m hypertext.lots.generation --phase export --series series/2026-Q1 --target playingcards
  python -m hypertext.lots.generation --phase grade --series series/2026-Q1 --parallel 2
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import signal
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


@dataclass
class LotDescription:
    """Description of what the LLM sees on a lot card."""
    # Header
    lot_badge_visible: bool
    lot_badge_text: str
    card_count_label_visible: bool
    card_count_label_text: str
    card_count_value: str  # e.g., "5-CARD"
    # Title
    phase_name: str
    flavor_text: str
    # Reward
    reward_text: str  # e.g., "REWARD: 8 Points"
    wreath_bonus_text: str  # Should be "Wreath Bonus: +2 Points (First to record)"
    # Composition
    composition_has_icons: bool
    composition_has_brackets: bool  # True if [NOUN] style, False if just NOUN - should be False
    composition_display: str
    # Context
    context_header_visible: bool
    context_text: str
    # Footer
    series_footer: str
    # Styling
    color_scheme_matches: bool
    frame_style_matches: bool
    all_sections_present: bool
    missing_or_wrong: list[str]
    # Style match (CRITICAL)
    style_matches_reference: bool  # False = automatic fail
    style_mismatch_reason: str
    raw_response: str = ""


@dataclass
class LotGradeResult:
    """Result of grading a lot card."""
    lot_id: int
    phase_name: str
    score: int  # 0-100
    passed: bool
    issues: list[str]
    description: Optional[LotDescription] = None


LOT_DESCRIBE_PROMPT = """You are comparing a TEST card against REFERENCE style images.

## IMAGE LABELS:
{image_labels}

## TASK 1: Analyze REFERENCE style (images [1] through [{ref_count}])

These are the CORRECT reference templates. Note their:
- Border style (straight rectangular vs ornate curly corners)
- Reward section shape (floating ribbon vs full-width bar)
- Context header style (solid navy bar vs text between lines)
- Composition area style (bracket corners vs boxed header)

## TASK 2: Analyze TEST card (image [{test_idx}])

Describe what you see on the test card:
- Header badges (LOT badge, CARD COUNT)
- Title and subtitle
- Reward banner shape and text
- Composition section (icons, type labels)
  - NOTE: Only check if the TEXT itself has square bracket characters like "[NOUN]"
  - Decorative boxes, containers, or frames around the section are NOT "brackets"
- Context section header style
- Border style
- Footer

## TASK 3: Compare structures

The TEST card is a STYLE MISMATCH if ANY of these differ from references:
- Border shape (ornate/curly vs straight/rectangular)
- Reward element shape (bar vs ribbon)
- Context header style (lines vs solid block)
- Overall layout structure

## TASK 4: Return JSON

Return ONLY this JSON (no other text):
```json
{{
  "lot_badge_visible": true|false,
  "lot_badge_text": "<text in left badge>",
  "card_count_label_visible": true|false,
  "card_count_label_text": "<exact label text>",
  "card_count_value": "<value like '5-CARD'>",
  "phase_name": "<main title>",
  "flavor_text": "<italic subtitle>",
  "reward_text": "<full reward line>",
  "wreath_bonus_text": "<exact wreath bonus text>",
  "composition_has_icons": true|false,
  "composition_has_brackets": true|false,  // ONLY true if text literally shows "[NOUN]" - decorative boxes/containers don't count
  "composition_display": "<what's shown>",
  "context_header_visible": true|false,
  "context_text": "<first 50 chars...>",
  "series_footer": "<footer text>",
  "color_scheme_matches": true|false,
  "frame_style_matches": true|false,
  "all_sections_present": true|false,
  "missing_or_wrong": ["list any issues"],
  "style_matches_reference": true|false,
  "style_mismatch_reason": "<if false, explain structural differences from references>"
}}
```
"""


LOT_SCORE_TEMPLATE = """Score this LOT card based on what was observed vs expected.

## EXPECTED (from reference style):
- Phase Name: {phase_name}
- Card Count: "{cards}-CARD" with "CARD COUNT" label above it
- Reward: "REWARD: {points} Points"
- Wreath Bonus: "Wreath Bonus: +2 Points (First to record)" - note lowercase "record"
- Composition: Icons with type labels like NOUN + VERB (NO square brackets around type names)
- Context: Navy "CONTEXT" header bar with text below
- Footer: "SERIES: 2026-Q1 Lots"
- Style: Antique parchment aesthetic, navy/gold colors, structured card layout

## OBSERVED:
{description_json}

## AUTOMATIC FAIL CONDITIONS:
- style_matches_reference = false → AUTOMATIC FAIL (score 0, passed=false)
  A card with wrong art style, wrong colors, or wrong layout structure fails immediately.

## RUBRIC (100 points) - Only scored if style matches:

### HEADER (20 pts)
- "LOT" badge visible in top-left (5 pts)
- "CARD COUNT" label visible above X-CARD value (10 pts) - CRITICAL
- Correct card count value "{cards}-CARD" (5 pts)

### TITLE & FLAVOR (15 pts)
- Phase name "{phase_name}" matches (10 pts)
- Italic flavor/subtitle present (5 pts)

### REWARD BANNER (20 pts)
- "REWARD: {points} Points" correct (10 pts)
- Wreath bonus includes "(First to record)" (10 pts) - CRITICAL

### COMPOSITION (15 pts)
- Has icons for card types (5 pts)
- Card type labels displayed (NOUN, VERB, etc.) (5 pts)
  - ONLY deduct if the TEXT literally has square bracket characters: "[NOUN]"
  - Decorative boxes, containers, or frames around the area are fine - those are NOT brackets
- Proper + symbols between types (5 pts)

### CONTEXT (15 pts)
- "CONTEXT" header bar visible (10 pts)
- Context text present below (5 pts)

### STYLING (15 pts)
- Navy/gold/parchment color scheme (5 pts)
- Double border frame style (5 pts)
- Series footer present (5 pts)

Pass threshold: 80 points with no CRITICAL failures.

Return JSON:
```json
{{
  "score": <0-100>,
  "passed": true|false,
  "issues": ["issue1", "issue2"]
}}
```
"""


def _read_image_bytes(path: str) -> bytes:
    """Read image file as bytes."""
    with open(path, "rb") as f:
        return f.read()


def _image_part_from_bytes(img_bytes: bytes):
    """Create a Gemini Part from image bytes."""
    if types is None:
        raise RuntimeError("google-genai package not found. Install with: pip install google-genai")

    image_part = None

    if hasattr(types.Part, "from_bytes"):
        try:
            image_part = types.Part.from_bytes(data=img_bytes, mime_type="image/png")
        except Exception:
            pass

    if image_part is None and hasattr(types.Part, "from_image"):
        try:
            image_part = types.Part.from_image(image=img_bytes, mime_type="image/png")
        except Exception:
            pass

    if image_part is None:
        try:
            blob_cls = getattr(types, "Blob", None)
            if blob_cls:
                image_part = types.Part(inline_data=blob_cls(data=img_bytes, mime_type="image/png"))
            else:
                image_part = types.Part(
                    inline_data={"mime_type": "image/png", "data": img_bytes}
                )
        except Exception as e:
            raise RuntimeError(f"Failed to construct image part: {e}")

    return image_part


GRADING_MODEL = "gemini-3-pro-preview"  # Vision model for grading


def describe_style_references(series_dir: Path) -> str:
    """Describe the style reference images to establish the grading rubric.

    Args:
        series_dir: Path to series directory

    Returns:
        Text description of what a correct LOT card looks like
    """
    if genai is None or types is None:
        raise RuntimeError("google-genai package required: pip install google-genai")

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_TEXT_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY env var not set")

    # Find style references
    from hypertext.lots.renderer import _build_lot_style_refs
    style_refs = _build_lot_style_refs(series_dir)

    if not style_refs:
        return "No style references found. Using default rubric."

    client = genai.Client(api_key=api_key)

    # Build image parts for all refs (max 3)
    refs_to_use = style_refs[:3]
    image_parts = []
    ref_labels = []
    for i, ref_path in enumerate(refs_to_use, 1):
        img_bytes = _read_image_bytes(ref_path)
        image_parts.append(_image_part_from_bytes(img_bytes))
        ref_name = Path(ref_path).name
        ref_labels.append(f"[{i}] {ref_name}")

    # Build prompt with labeled references
    labels_text = "\n".join(ref_labels)
    prompt = f"""You are provided {len(refs_to_use)} LOT card reference images:
{labels_text}

Examine each image and describe the EXACT visual style that defines a correctly rendered LOT card.

For each card, describe:
1. HEADER: What badges/labels are visible? Where are they positioned? What text do they contain?
2. TITLE AREA: How is the phase name styled? Is there a subtitle?
3. REWARD SECTION: What does the reward banner look like? What exact text appears?
4. COMPOSITION AREA: How are card type requirements displayed? Are there icons? Brackets?
5. CONTEXT SECTION: Where is the educational text? How is it formatted?
6. FOOTER: What information appears at the bottom?
7. FRAME/COLORS: What colors are used? Navy/gold/parchment scheme?

Be SPECIFIC about what you see - this will be used as the grading rubric for other cards."""

    contents = [*image_parts, types.Part.from_text(text=prompt)]

    try:
        response = client.models.generate_content(
            model=GRADING_MODEL,
            contents=contents,
        )
    except Exception as e:
        _log(f"Error describing style references: {e}")
        return "Error analyzing style references."

    if not response.candidates:
        return "No description generated."

    candidate = response.candidates[0]
    parts = (candidate.content.parts if candidate.content and candidate.content.parts else [])

    text_content = ""
    for part in parts:
        if hasattr(part, "text") and part.text:
            text_content += part.text

    return text_content or "No description generated."


def describe_lot_card(image_path: Path, style_refs: list[str] | None = None) -> Optional[LotDescription]:
    """Use Gemini to describe what's visible on a lot card image.

    Args:
        image_path: Path to the lot card PNG
        style_refs: List of style reference image paths for comparison

    Returns:
        LotDescription with observed details, or None on error
    """
    if genai is None or types is None:
        raise RuntimeError("google-genai package required: pip install google-genai")

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_TEXT_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY env var not set")

    client = genai.Client(api_key=api_key)

    # Build image parts: refs first, then test card
    image_parts = []
    labels = []

    if style_refs:
        for i, ref_path in enumerate(style_refs, 1):
            ref_bytes = _read_image_bytes(ref_path)
            image_parts.append(_image_part_from_bytes(ref_bytes))
            ref_name = Path(ref_path).name
            labels.append(f"[{i}] REFERENCE: {ref_name}")

    # Add the test card
    test_idx = len(style_refs or []) + 1
    img_bytes = _read_image_bytes(str(image_path))
    image_parts.append(_image_part_from_bytes(img_bytes))
    labels.append(f"[{test_idx}] TEST CARD: {image_path.name}")

    # Format prompt with image labels
    ref_count = len(style_refs or [])
    prompt = LOT_DESCRIBE_PROMPT.format(
        image_labels="\n".join(labels),
        ref_count=ref_count if ref_count > 0 else 1,
        test_idx=test_idx,
    )

    contents = [*image_parts, types.Part.from_text(text=prompt)]

    try:
        response = client.models.generate_content(
            model=GRADING_MODEL,
            contents=contents,
        )
    except Exception as e:
        _log(f"Gemini API error: {e}")
        return None

    if not response.candidates:
        _log("No candidates returned from Gemini")
        return None

    candidate = response.candidates[0]
    parts = (candidate.content.parts if candidate.content and candidate.content.parts else [])

    text_content = ""
    for part in parts:
        if hasattr(part, "text") and part.text:
            text_content += part.text

    if not text_content:
        _log("No text response from Gemini")
        return None

    # Parse JSON from response
    try:
        # Extract JSON from markdown code block if present
        if "```json" in text_content:
            json_start = text_content.find("```json") + 7
            json_end = text_content.find("```", json_start)
            json_str = text_content[json_start:json_end].strip()
        elif "```" in text_content:
            json_start = text_content.find("```") + 3
            json_end = text_content.find("```", json_start)
            json_str = text_content[json_start:json_end].strip()
        else:
            json_str = text_content.strip()

        data = json.loads(json_str)

        return LotDescription(
            # Header
            lot_badge_visible=data.get("lot_badge_visible", False),
            lot_badge_text=data.get("lot_badge_text", ""),
            card_count_label_visible=data.get("card_count_label_visible", False),
            card_count_label_text=data.get("card_count_label_text", ""),
            card_count_value=data.get("card_count_value", ""),
            # Title
            phase_name=data.get("phase_name", ""),
            flavor_text=data.get("flavor_text", ""),
            # Reward
            reward_text=data.get("reward_text", ""),
            wreath_bonus_text=data.get("wreath_bonus_text", ""),
            # Composition
            composition_has_icons=data.get("composition_has_icons", False),
            composition_has_brackets=data.get("composition_has_brackets", False),
            composition_display=data.get("composition_display", ""),
            # Context
            context_header_visible=data.get("context_header_visible", False),
            context_text=data.get("context_text", ""),
            # Footer
            series_footer=data.get("series_footer", ""),
            # Styling
            color_scheme_matches=data.get("color_scheme_matches", True),
            frame_style_matches=data.get("frame_style_matches", True),
            all_sections_present=data.get("all_sections_present", True),
            missing_or_wrong=data.get("missing_or_wrong", []),
            # Style match (CRITICAL)
            style_matches_reference=data.get("style_matches_reference", True),
            style_mismatch_reason=data.get("style_mismatch_reason", ""),
            raw_response=text_content,
        )
    except json.JSONDecodeError as e:
        _log(f"Failed to parse JSON response: {e}")
        _log(f"Raw response: {text_content[:500]}")
        return None


def score_lot_card(
    description: LotDescription,
    phase_data: dict[str, Any],
) -> LotGradeResult:
    """Score a lot card against the rubric based on its description.

    Args:
        description: LotDescription from describe_lot_card()
        phase_data: Phase metadata (id, name, cards, points, display)

    Returns:
        LotGradeResult with score and issues
    """
    if genai is None or types is None:
        raise RuntimeError("google-genai package required: pip install google-genai")

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_TEXT_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY env var not set")

    client = genai.Client(api_key=api_key)

    lot_id = phase_data.get("id", 0)
    phase_name = phase_data.get("name", "UNKNOWN")
    cards = phase_data.get("cards", 5)
    points = phase_data.get("points", 8)
    display = phase_data.get("display", "")

    # Check for automatic style mismatch fail
    if not description.style_matches_reference:
        reason = description.style_mismatch_reason or "Style does not match reference"
        return LotGradeResult(
            lot_id=lot_id,
            phase_name=phase_name,
            score=0,
            passed=False,
            issues=[f"STYLE MISMATCH (automatic fail): {reason}"],
            description=description,
        )

    # Convert description to JSON for the prompt
    desc_dict = {
        # Header
        "lot_badge_visible": description.lot_badge_visible,
        "lot_badge_text": description.lot_badge_text,
        "card_count_label_visible": description.card_count_label_visible,
        "card_count_label_text": description.card_count_label_text,
        "card_count_value": description.card_count_value,
        # Title
        "phase_name": description.phase_name,
        "flavor_text": description.flavor_text,
        # Reward
        "reward_text": description.reward_text,
        "wreath_bonus_text": description.wreath_bonus_text,
        # Composition
        "composition_has_icons": description.composition_has_icons,
        "composition_has_brackets": description.composition_has_brackets,
        "composition_display": description.composition_display,
        # Context
        "context_header_visible": description.context_header_visible,
        "context_text": description.context_text,
        # Footer
        "series_footer": description.series_footer,
        # Styling
        "color_scheme_matches": description.color_scheme_matches,
        "frame_style_matches": description.frame_style_matches,
        "all_sections_present": description.all_sections_present,
        "missing_or_wrong": description.missing_or_wrong,
        # Style match
        "style_matches_reference": description.style_matches_reference,
        "style_mismatch_reason": description.style_mismatch_reason,
    }

    prompt = LOT_SCORE_TEMPLATE.format(
        phase_name=phase_name,
        cards=cards,
        points=points,
        description_json=json.dumps(desc_dict, indent=2),
    )

    try:
        response = client.models.generate_content(
            model=GRADING_MODEL,
            contents=[types.Part.from_text(text=prompt)],
        )
    except Exception as e:
        _log(f"Gemini API error: {e}")
        return LotGradeResult(
            lot_id=lot_id,
            phase_name=phase_name,
            score=0,
            passed=False,
            issues=[f"API error: {e}"],
            description=description,
        )

    if not response.candidates:
        return LotGradeResult(
            lot_id=lot_id,
            phase_name=phase_name,
            score=0,
            passed=False,
            issues=["No response from grading model"],
            description=description,
        )

    candidate = response.candidates[0]
    parts = (candidate.content.parts if candidate.content and candidate.content.parts else [])

    text_content = ""
    for part in parts:
        if hasattr(part, "text") and part.text:
            text_content += part.text

    # Parse JSON from response
    try:
        if "```json" in text_content:
            json_start = text_content.find("```json") + 7
            json_end = text_content.find("```", json_start)
            json_str = text_content[json_start:json_end].strip()
        elif "```" in text_content:
            json_start = text_content.find("```") + 3
            json_end = text_content.find("```", json_start)
            json_str = text_content[json_start:json_end].strip()
        else:
            json_str = text_content.strip()

        data = json.loads(json_str)

        return LotGradeResult(
            lot_id=lot_id,
            phase_name=phase_name,
            score=data.get("score", 0),
            passed=data.get("passed", False),
            issues=data.get("issues", []),
            description=description,
        )
    except json.JSONDecodeError as e:
        _log(f"Failed to parse score JSON: {e}")
        return LotGradeResult(
            lot_id=lot_id,
            phase_name=phase_name,
            score=0,
            passed=False,
            issues=[f"JSON parse error: {e}", f"Raw: {text_content[:200]}"],
            description=description,
        )


def phase_grade(series_dir: Path, parallel: int = 1, describe_refs: bool = True) -> int:
    """Grade rendered lot cards against the rubric.

    Args:
        series_dir: Path to series directory
        parallel: Number of concurrent grading operations (default 1)
        describe_refs: If True, first describe the style references

    Returns:
        0 if all cards pass, 1 if any fail or errors occur
    """
    if yaml is None:
        _log("Error: pyyaml required. Install with: pip install pyyaml")
        return 1

    phases = load_universal_phases()
    lots_dir = series_dir / "lots"

    # Load style references once for all grading
    from hypertext.lots.renderer import _build_lot_style_refs
    style_refs = _build_lot_style_refs(series_dir)
    if style_refs:
        _log(f"Loaded {len(style_refs)} style reference(s) for comparison:")
        for ref in style_refs:
            _log(f"  - {Path(ref).name}")
    else:
        _log("WARNING: No style references found - style matching will be less accurate")

    # Find rendered lots
    rendered_lots: list[tuple[dict, Path]] = []
    for phase in phases:
        pid = phase["id"]
        name = phase["name"]
        slug = name.lower().replace(" ", "-")
        lot_dir = lots_dir / f"{pid:02d}-{slug}"
        out_path = lot_dir / "outputs" / "lot_1024x1536.png"
        if out_path.exists():
            rendered_lots.append((phase, out_path))

    if not rendered_lots:
        _log("No rendered lots found to grade")
        return 1

    # First, describe the style references to establish the rubric
    if describe_refs:
        _log("")
        _log("=" * 60)
        _log("ANALYZING STYLE REFERENCES")
        _log("=" * 60)
        ref_description = describe_style_references(series_dir)
        _log(ref_description)
        _log("=" * 60)
        _log("")

        # Save the reference description
        rubric_path = lots_dir / "grading_rubric.txt"
        with open(rubric_path, "w", encoding="utf-8") as f:
            f.write("LOT CARD GRADING RUBRIC\n")
            f.write("Generated from style reference images\n")
            f.write("=" * 60 + "\n\n")
            f.write(ref_description)
        _log(f"Rubric saved to {rubric_path}\n")

    _log(f"Grading {len(rendered_lots)} lot cards using {GRADING_MODEL}...")

    results: list[LotGradeResult] = []
    semaphore = threading.Semaphore(max(1, min(parallel, 4)))

    def grade_single(phase: dict, image_path: Path) -> LotGradeResult:
        pid = phase["id"]
        name = phase["name"]
        _log(f"[{pid:02d}] Grading {name}...")

        with semaphore:
            description = describe_lot_card(image_path, style_refs=style_refs)
            if description is None:
                result = LotGradeResult(
                    lot_id=pid,
                    phase_name=name,
                    score=0,
                    passed=False,
                    issues=["Failed to describe card"],
                )
            else:
                result = score_lot_card(description, phase)

        # Save grade.json next to the card
        lot_dir = image_path.parent.parent  # outputs/ -> lot_dir/
        grade_json = lot_dir / "grade.json"
        grade_data = {
            "lot_id": result.lot_id,
            "phase_name": result.phase_name,
            "score": result.score,
            "passed": result.passed,
            "issues": result.issues,
        }
        with open(grade_json, "w", encoding="utf-8") as f:
            json.dump(grade_data, f, indent=2)

        # Save grade.txt with readable summary
        grade_txt = lot_dir / "grade.txt"
        status = "PASS" if result.passed else "FAIL"
        lines = [
            f"LOT CARD GRADE",
            f"==============",
            f"Phase: {result.phase_name}",
            f"Lot ID: {result.lot_id:02d}",
            f"Score: {result.score}/100",
            f"Status: {status}",
            f"",
        ]
        if result.issues:
            lines.append("Issues:")
            for issue in result.issues:
                lines.append(f"  - {issue}")
        else:
            lines.append("No issues found.")
        with open(grade_txt, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        return result

    if parallel == 1:
        for phase, image_path in rendered_lots:
            result = grade_single(phase, image_path)
            results.append(result)
    else:
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {
                executor.submit(grade_single, phase, image_path): phase["id"]
                for phase, image_path in rendered_lots
            }
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    pid = futures[future]
                    _log(f"[{pid:02d}] Unexpected error: {e}")
                    results.append(LotGradeResult(
                        lot_id=pid,
                        phase_name="UNKNOWN",
                        score=0,
                        passed=False,
                        issues=[str(e)],
                    ))

    # Sort results by lot_id
    results.sort(key=lambda r: r.lot_id)

    # Print results
    _log("\n" + "=" * 60)
    _log("LOT CARD GRADING RESULTS")
    _log("=" * 60)

    passed_count = 0
    failed_count = 0

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        status_icon = "✓" if result.passed else "✗"
        _log(f"\n[{result.lot_id:02d}] {result.phase_name}: {status_icon} {status} (Score: {result.score}/100)")

        if result.issues:
            for issue in result.issues:
                _log(f"     - {issue}")

        if result.passed:
            passed_count += 1
        else:
            failed_count += 1

    _log("\n" + "-" * 60)
    _log(f"SUMMARY: {passed_count} passed, {failed_count} failed out of {len(results)} graded")
    _log("-" * 60)

    # Save results to JSON
    results_path = lots_dir / "grade_results.json"
    results_data = [
        {
            "lot_id": r.lot_id,
            "phase_name": r.phase_name,
            "score": r.score,
            "passed": r.passed,
            "issues": r.issues,
        }
        for r in results
    ]
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)
    _log(f"\nResults saved to {results_path}")

    return 0 if failed_count == 0 else 1


_shutdown_requested = False

def _setup_interrupt_handler() -> None:
    """Setup handler for immediate exit on Ctrl+C."""
    def handler(signum, frame):
        global _shutdown_requested
        _shutdown_requested = True
        print("\nInterrupted - exiting immediately", file=sys.stderr)
        # Force immediate exit, bypassing thread cleanup
        os._exit(1)

    # Set handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, handler)
    # Also handle SIGTERM if available
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, handler)

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

# Package paths
PACKAGE_DIR = Path(__file__).resolve().parent.parent
TOOLS_DIR = PACKAGE_DIR.parent
PROJECT_ROOT = TOOLS_DIR.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
UNIVERSAL_PHASES_PATH = TEMPLATES_DIR / "phases.yml"


def _log(msg: str) -> None:
    """Log a message to stderr."""
    print(msg, file=sys.stderr)


def load_universal_phases() -> list[dict[str, Any]]:
    """Load universal phase definitions from templates/phases.yml."""
    if yaml is None:
        raise RuntimeError("pyyaml required: pip install pyyaml")
    if not UNIVERSAL_PHASES_PATH.exists():
        raise RuntimeError(f"Universal phases file not found: {UNIVERSAL_PHASES_PATH}")
    with open(UNIVERSAL_PHASES_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("phases", [])


def load_series_content(series_dir: Path) -> dict[int, dict[str, str]]:
    """Load series-specific flavor/context from lot_content.yml."""
    if yaml is None:
        raise RuntimeError("pyyaml required: pip install pyyaml")
    content_path = series_dir / "lots" / "lot_content.yml"
    if not content_path.exists():
        return {}
    with open(content_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("content", {})


def get_series_theme(series_dir: Path) -> str:
    """Get theme from series stats.yml."""
    if yaml is None:
        raise RuntimeError("pyyaml required: pip install pyyaml")
    stats_path = series_dir / "stats.yml"
    if not stats_path.exists():
        return ""
    with open(stats_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("theme", "")


def phase_init(series_dir: Path) -> int:
    """Create lot_content.yml template with empty flavor/context for all 30 phases."""
    if yaml is None:
        _log("Error: pyyaml required. Install with: pip install pyyaml")
        return 1

    lots_dir = series_dir / "lots"
    lots_dir.mkdir(parents=True, exist_ok=True)

    content_path = lots_dir / "lot_content.yml"
    if content_path.exists():
        _log(f"{content_path} already exists. Delete to regenerate.")
        return 1

    phases = load_universal_phases()
    theme = get_series_theme(series_dir)

    content: dict[str, Any] = {
        "series": series_dir.name,
        "theme": theme,
        "content": {}
    }

    for phase in phases:
        content["content"][phase["id"]] = {
            "flavor": "",
            "context": ""
        }

    with open(content_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(content, f, sort_keys=False, allow_unicode=True, default_flow_style=False)

    _log(f"Created {content_path} with {len(phases)} empty entries.")
    return 0


def _save_content(content_path: Path, data: dict, lock: Optional[threading.Lock] = None) -> None:
    """Thread-safe save of lot_content.yml."""
    if lock:
        with lock:
            with open(content_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=80, default_flow_style=False)
    else:
        with open(content_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=80, default_flow_style=False)


def _generate_single_phase_content(
    phase: dict,
    theme: str,
    semaphore: threading.Semaphore,
    generate_text_func,
) -> tuple[int, str, str, Optional[str]]:
    """Generate flavor and context for a single phase. Returns (pid, flavor, context, error)."""
    pid = phase["id"]
    name = phase["name"]

    _log(f"[{pid:02d}] {name}: generating...")

    with semaphore:
        # Generate flavor
        flavor_prompt = f"""Generate a short, evocative flavor subtitle for a Biblical trading card game phase card.

Phase name: {name}
Card requirement: {phase['display']}
Series theme: {theme}

The flavor should:
- Be 5-12 words
- Sound poetic/biblical
- Connect to the phase name's meaning
- NOT explain the game mechanic

Return only the flavor text, no quotes or explanation."""

        try:
            flavor = generate_text_func(flavor_prompt, temperature=0.7).strip().strip('"')
        except Exception as e:
            _log(f"[{pid:02d}] Error generating flavor: {e}")
            return (pid, "", "", str(e))

        # Generate context
        context_prompt = f"""Generate a brief educational context for a Biblical trading card game phase card.

Phase name: {name}
Series theme: {theme}

The context should:
- Be 1-2 sentences only
- Explain the Biblical/theological significance of "{name}"
- Reference scripture if natural
- Match seminary-level tone

Return only the text, no quotes or explanation."""

        try:
            context = generate_text_func(context_prompt, temperature=0.5).strip().strip('"')
        except Exception as e:
            _log(f"[{pid:02d}] Error generating context: {e}")
            return (pid, flavor, "", str(e))

    if flavor:
        _log(f"[{pid:02d}] flavor: {flavor[:50]}...")

    return (pid, flavor, context, None)


def phase_generate(series_dir: Path, parallel: int = 1) -> int:
    """Use Gemini to generate flavor text and context for each phase.

    Args:
        series_dir: Path to series directory
        parallel: Number of concurrent generations (default 1)
    """
    if yaml is None:
        _log("Error: pyyaml required. Install with: pip install pyyaml")
        return 1

    # Import from package
    try:
        from hypertext.gemini.text import generate_text
    except ImportError:
        # Fallback to old location
        sys.path.insert(0, str(TOOLS_DIR))
        try:
            from gemini_text import generate_text
        except ImportError as e:
            _log(f"Error importing gemini_text: {e}")
            return 1

    phases = load_universal_phases()
    theme = get_series_theme(series_dir)
    content_path = series_dir / "lots" / "lot_content.yml"

    if not content_path.exists():
        _log(f"Run --phase init first to create {content_path}")
        return 1

    with open(content_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    existing_content = data.get("content", {})

    # Filter to phases that need generation
    phases_to_generate = []
    skipped_count = 0
    for phase in phases:
        pid = phase["id"]
        name = phase["name"]
        entry = existing_content.get(pid, {})
        if entry.get("flavor") and entry.get("context"):
            _log(f"[{pid:02d}] {name}: already has content, skipping")
            skipped_count += 1
        else:
            phases_to_generate.append(phase)

    if not phases_to_generate:
        _log(f"All {len(phases)} phases already have content")
        return 0

    # Clamp parallel to reasonable bounds
    parallel = max(1, min(parallel, 8))
    _log(f"Generating content for {len(phases_to_generate)} phases with {parallel} worker(s)...")

    semaphore = threading.Semaphore(parallel)
    content_lock = threading.Lock()
    generated_count = 0
    error_count = 0

    def process_result(pid: int, flavor: str, context: str, error: Optional[str]) -> None:
        nonlocal generated_count, error_count
        if error:
            error_count += 1
            return

        with content_lock:
            existing_content[pid] = {"flavor": flavor, "context": context}
            data["content"] = existing_content
            _save_content(content_path, data, lock=None)  # Already holding lock
            generated_count += 1
            _log(f"[{pid:02d}] saved ({generated_count} generated, {skipped_count} skipped)")

    if parallel == 1:
        # Sequential
        for phase in phases_to_generate:
            pid, flavor, context, error = _generate_single_phase_content(
                phase, theme, semaphore, generate_text
            )
            process_result(pid, flavor, context, error)
    else:
        # Parallel
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {
                executor.submit(
                    _generate_single_phase_content,
                    phase, theme, semaphore, generate_text
                ): phase["id"]
                for phase in phases_to_generate
            }

            for future in as_completed(futures):
                try:
                    pid, flavor, context, error = future.result()
                    process_result(pid, flavor, context, error)
                except Exception as e:
                    pid = futures[future]
                    _log(f"[{pid:02d}] Unexpected error: {e}")
                    error_count += 1

    _log(f"Completed: {generated_count} generated, {skipped_count} skipped, {error_count} errors")
    return 0 if error_count == 0 else 1


def _render_single_lot(
    phase: dict,
    content: dict[int, dict[str, str]],
    theme: str,
    series_dir: Path,
    lots_dir: Path,
    semaphore: threading.Semaphore,
    render_func,
) -> tuple[int, Optional[str]]:
    """Render a single lot card. Returns (phase_id, error_message or None)."""
    pid = phase["id"]
    name = phase["name"]
    slug = name.lower().replace(" ", "-")

    card_dir = lots_dir / f"{pid:02d}-{slug}"
    card_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir = card_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    phase_content = content.get(pid, {})

    card_data = {
        **phase,
        "flavor": phase_content.get("flavor", ""),
        "context": phase_content.get("context", ""),
        "series": series_dir.name,
        "theme": theme,
    }

    out_path = outputs_dir / "lot_1024x1536.png"

    _log(f"[{pid:02d}] Rendering {name}...")

    # Use semaphore to limit concurrent API calls
    with semaphore:
        try:
            render_func(card_data, out_path, series_dir)
        except Exception as e:
            _log(f"[{pid:02d}] Error rendering: {e}")
            return (pid, str(e))

    # Write meta.yml (outside semaphore - fast local I/O)
    meta = {
        "id": pid,
        "name": name,
        "cards": phase["cards"],
        "points": phase["points"],
        "display": phase["display"],
        "flavor": card_data["flavor"],
        "context": card_data["context"],
    }
    with open(card_dir / "meta.yml", "w", encoding="utf-8") as f:
        yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True, default_flow_style=False)

    _log(f"[{pid:02d}] Completed {name}")
    return (pid, None)


REVIEW_PASS_THRESHOLD = 90  # Minimum score to pass review
REVIEW_MAX_ATTEMPTS = 3  # Maximum render attempts per card


def _render_single_lot_with_review(
    phase: dict,
    content: dict[int, dict[str, str]],
    theme: str,
    series_dir: Path,
    lots_dir: Path,
    semaphore: threading.Semaphore,
    render_func,
    style_refs: list[str],
) -> tuple[int, Optional[str], int, int]:
    """Render a lot card with review loop. Re-renders if score < 90%.

    Returns (phase_id, error_message or None, final_score, attempts)
    """
    pid = phase["id"]
    name = phase["name"]
    slug = name.lower().replace(" ", "-")

    card_dir = lots_dir / f"{pid:02d}-{slug}"
    card_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir = card_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    phase_content = content.get(pid, {})

    card_data = {
        **phase,
        "flavor": phase_content.get("flavor", ""),
        "context": phase_content.get("context", ""),
        "series": series_dir.name,
        "theme": theme,
    }

    out_path = outputs_dir / "lot_1024x1536.png"
    prompt_path = card_dir / "prompt.txt"

    attempt = 0
    final_score = 0
    last_issues: list[str] = []

    while attempt < REVIEW_MAX_ATTEMPTS:
        attempt += 1
        _log(f"[{pid:02d}] Rendering {name} (attempt {attempt}/{REVIEW_MAX_ATTEMPTS})...")

        # Delete old output if exists (for re-renders)
        if out_path.exists():
            out_path.unlink()
        if prompt_path.exists():
            prompt_path.unlink()

        # Render with semaphore
        with semaphore:
            try:
                render_func(card_data, out_path, series_dir)
            except Exception as e:
                _log(f"[{pid:02d}] Error rendering: {e}")
                return (pid, str(e), 0, attempt)

            if not out_path.exists():
                _log(f"[{pid:02d}] Render produced no output")
                continue

            # Grade the card
            _log(f"[{pid:02d}] Grading {name}...")
            description = describe_lot_card(out_path, style_refs=style_refs)

            if description is None:
                _log(f"[{pid:02d}] Failed to describe card, retrying...")
                continue

            result = score_lot_card(description, phase)
            final_score = result.score
            last_issues = result.issues

            # Save grade
            grade_json = card_dir / "grade.json"
            grade_data = {
                "lot_id": result.lot_id,
                "phase_name": result.phase_name,
                "score": result.score,
                "passed": result.passed,
                "issues": result.issues,
                "attempt": attempt,
            }
            with open(grade_json, "w", encoding="utf-8") as f:
                json.dump(grade_data, f, indent=2)

            # Save grade.txt
            grade_txt = card_dir / "grade.txt"
            status = "PASS" if result.passed else "FAIL"
            lines = [
                f"LOT CARD GRADE",
                f"==============",
                f"Phase: {result.phase_name}",
                f"Lot ID: {result.lot_id:02d}",
                f"Score: {result.score}/100",
                f"Status: {status}",
                f"Attempt: {attempt}/{REVIEW_MAX_ATTEMPTS}",
                f"",
            ]
            if result.issues:
                lines.append("Issues:")
                for issue in result.issues:
                    lines.append(f"  - {issue}")
            else:
                lines.append("No issues found.")
            with open(grade_txt, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")

            if final_score >= REVIEW_PASS_THRESHOLD:
                _log(f"[{pid:02d}] PASSED with score {final_score}/100")
                break
            else:
                _log(f"[{pid:02d}] Score {final_score}/100 < {REVIEW_PASS_THRESHOLD}, retrying...")
                if last_issues:
                    for issue in last_issues[:3]:  # Show first 3 issues
                        _log(f"[{pid:02d}]   - {issue}")

    # Write meta.yml
    meta = {
        "id": pid,
        "name": name,
        "cards": phase["cards"],
        "points": phase["points"],
        "display": phase["display"],
        "flavor": card_data["flavor"],
        "context": card_data["context"],
        "render_attempts": attempt,
        "final_score": final_score,
    }
    with open(card_dir / "meta.yml", "w", encoding="utf-8") as f:
        yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True, default_flow_style=False)

    if final_score >= REVIEW_PASS_THRESHOLD:
        _log(f"[{pid:02d}] Completed {name} (score: {final_score}, attempts: {attempt})")
        return (pid, None, final_score, attempt)
    else:
        error_msg = f"Failed after {attempt} attempts (best score: {final_score})"
        _log(f"[{pid:02d}] {error_msg}")
        return (pid, error_msg, final_score, attempt)


def phase_render(series_dir: Path, parallel: int = 1, batch_size: str = "full", review: bool = False) -> int:
    """Render phase card PNGs using Gemini with style references.

    Args:
        series_dir: Path to series directory
        parallel: Number of concurrent renders (default 1, max 4 recommended)
        batch_size: How many to render - "single" (1), "quarter" (8), "half" (15), "full" (30)
        review: If True, grade each card and re-render if score < 90%
    """
    if yaml is None:
        _log("Error: pyyaml required. Install with: pip install pyyaml")
        return 1

    # Import from package
    try:
        from hypertext.lots.renderer import render_lot_card_with_series
    except ImportError:
        # Fallback to old location
        sys.path.insert(0, str(TOOLS_DIR))
        try:
            from lot_renderer import render_lot_card_with_series
        except ImportError as e:
            _log(f"Error importing lot_renderer: {e}")
            _log("Make sure lot_renderer.py exists in the tools directory.")
            return 1

    phases = load_universal_phases()
    content = load_series_content(series_dir)
    theme = get_series_theme(series_dir)
    lots_dir = series_dir / "lots"

    # Calculate batch limit
    batch_limits = {"single": 1, "quarter": 8, "half": 15, "full": 30}
    limit = batch_limits.get(batch_size, 30)

    # Find phases that need rendering (no existing image)
    phases_to_render = []
    already_rendered = 0
    for phase in phases:
        pid = phase["id"]
        name = phase["name"]
        slug = name.lower().replace(" ", "-")
        out_path = lots_dir / f"{pid:02d}-{slug}" / "outputs" / "lot_1024x1536.png"
        if out_path.exists():
            already_rendered += 1
        else:
            phases_to_render.append(phase)

    _log(f"Found {already_rendered} already rendered, {len(phases_to_render)} pending")

    # Apply batch limit
    if len(phases_to_render) > limit:
        phases_to_render = phases_to_render[:limit]
        _log(f"Batch size '{batch_size}': rendering {limit} of {len(phases) - already_rendered} pending")

    if not phases_to_render:
        _log("All lots already rendered")
        return 0

    # Clamp parallel to reasonable bounds
    parallel = max(1, min(parallel, 8))

    # Load style refs if review mode enabled
    style_refs: list[str] = []
    if review:
        from hypertext.lots.renderer import _build_lot_style_refs
        style_refs = _build_lot_style_refs(series_dir)
        if style_refs:
            _log(f"Review mode: loaded {len(style_refs)} style reference(s)")
        else:
            _log("WARNING: No style references found for review mode")
        _log(f"Rendering {len(phases_to_render)} lot cards with review (threshold: {REVIEW_PASS_THRESHOLD}%, max attempts: {REVIEW_MAX_ATTEMPTS})...")
    else:
        _log(f"Rendering {len(phases_to_render)} lot cards with {parallel} worker(s)...")

    # Semaphore limits concurrent Gemini API calls
    semaphore = threading.Semaphore(parallel)

    rendered_count = 0
    error_count = 0
    errors: list[tuple[int, str]] = []
    total_attempts = 0
    scores: list[int] = []

    if review:
        # Render with review loop (sequential only for now - review is expensive)
        for phase in phases_to_render:
            pid, error, score, attempts = _render_single_lot_with_review(
                phase, content, theme, series_dir, lots_dir, semaphore,
                render_lot_card_with_series, style_refs
            )
            total_attempts += attempts
            if error:
                errors.append((pid, error))
                error_count += 1
            else:
                rendered_count += 1
            scores.append(score)
    elif parallel == 1:
        # Sequential rendering (original behavior)
        for phase in phases_to_render:
            pid, error = _render_single_lot(
                phase, content, theme, series_dir, lots_dir, semaphore, render_lot_card_with_series
            )
            if error:
                errors.append((pid, error))
                error_count += 1
            else:
                rendered_count += 1
    else:
        # Parallel rendering with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {
                executor.submit(
                    _render_single_lot,
                    phase, content, theme, series_dir, lots_dir, semaphore, render_lot_card_with_series
                ): phase["id"]
                for phase in phases_to_render
            }

            for future in as_completed(futures):
                pid = futures[future]
                try:
                    result_pid, error = future.result()
                    if error:
                        errors.append((result_pid, error))
                        error_count += 1
                    else:
                        rendered_count += 1
                except Exception as e:
                    _log(f"[{pid:02d}] Unexpected error: {e}")
                    errors.append((pid, str(e)))
                    error_count += 1

    _log(f"Rendered {rendered_count} lot cards to {lots_dir}")
    if review and scores:
        avg_score = sum(scores) / len(scores)
        _log(f"  Average score: {avg_score:.1f}/100, Total attempts: {total_attempts}")
    if error_count:
        _log(f"  ({error_count} errors)")
        for pid, err in sorted(errors):
            _log(f"    [{pid:02d}]: {err[:80]}")
    return 0 if error_count == 0 else 1


def phase_rebuild(series_dir: Path, batch_size: str = "full", parallel: int = 1) -> int:
    """Force rebuild all lot cards with grading and retry loop.

    Unlike render, this deletes existing outputs and regenerates everything.
    Each card is graded after rendering and re-rendered if score < 90%.

    Args:
        series_dir: Path to series directory
        batch_size: How many to rebuild - "single" (1), "quarter" (8), "half" (15), "full" (30)
        parallel: Number of concurrent rebuilds (default 1, max 4 recommended)
    """
    if yaml is None:
        _log("Error: pyyaml required. Install with: pip install pyyaml")
        return 1

    # Import renderer
    try:
        from hypertext.lots.renderer import render_lot_card_with_series, _build_lot_style_refs
    except ImportError:
        sys.path.insert(0, str(TOOLS_DIR))
        try:
            from lot_renderer import render_lot_card_with_series
            from lot_renderer import _build_lot_style_refs
        except ImportError as e:
            _log(f"Error importing lot_renderer: {e}")
            return 1

    phases = load_universal_phases()
    content = load_series_content(series_dir)
    theme = get_series_theme(series_dir)
    lots_dir = series_dir / "lots"

    # Load style refs for grading
    style_refs = _build_lot_style_refs(series_dir)
    if style_refs:
        _log(f"Loaded {len(style_refs)} style reference(s) for grading")
    else:
        _log("WARNING: No style references found - grading will be less accurate")

    # Calculate batch limit
    batch_limits = {"single": 1, "quarter": 8, "half": 15, "full": 30}
    limit = batch_limits.get(batch_size, 30)

    # Select phases to rebuild
    phases_to_rebuild = phases[:limit]

    # Clamp parallel to reasonable bounds
    parallel = max(1, min(parallel, 4))

    _log(f"REBUILD: Force re-rendering {len(phases_to_rebuild)} lot cards with grading...")
    _log(f"  Threshold: {REVIEW_PASS_THRESHOLD}%, Max attempts: {REVIEW_MAX_ATTEMPTS}, Workers: {parallel}")

    # Delete existing outputs for selected phases
    for phase in phases_to_rebuild:
        pid = phase["id"]
        name = phase["name"]
        slug = name.lower().replace(" ", "-")
        card_dir = lots_dir / f"{pid:02d}-{slug}"
        out_path = card_dir / "outputs" / "lot_1024x1536.png"
        prompt_path = card_dir / "prompt.txt"
        grade_json = card_dir / "grade.json"
        grade_txt = card_dir / "grade.txt"

        # Delete existing files
        for f in [out_path, prompt_path, grade_json, grade_txt]:
            if f.exists():
                f.unlink()

    _log(f"Deleted existing outputs for {len(phases_to_rebuild)} cards")

    # Semaphore for API rate limiting
    semaphore = threading.Semaphore(parallel)

    rendered_count = 0
    error_count = 0
    errors: list[tuple[int, str]] = []
    total_attempts = 0
    scores: list[int] = []

    if parallel == 1:
        # Sequential
        for phase in phases_to_rebuild:
            pid, error, score, attempts = _render_single_lot_with_review(
                phase, content, theme, series_dir, lots_dir, semaphore,
                render_lot_card_with_series, style_refs
            )
            total_attempts += attempts
            scores.append(score)
            if error:
                errors.append((pid, error))
                error_count += 1
            else:
                rendered_count += 1
    else:
        # Parallel with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {
                executor.submit(
                    _render_single_lot_with_review,
                    phase, content, theme, series_dir, lots_dir, semaphore,
                    render_lot_card_with_series, style_refs
                ): phase["id"]
                for phase in phases_to_rebuild
            }

            for future in as_completed(futures):
                pid = futures[future]
                try:
                    result_pid, error, score, attempts = future.result()
                    total_attempts += attempts
                    scores.append(score)
                    if error:
                        errors.append((result_pid, error))
                        error_count += 1
                    else:
                        rendered_count += 1
                except Exception as e:
                    _log(f"[{pid:02d}] Unexpected error: {e}")
                    errors.append((pid, str(e)))
                    error_count += 1

    # Summary
    _log("")
    _log("=" * 60)
    _log("REBUILD COMPLETE")
    _log("=" * 60)
    _log(f"Rebuilt: {rendered_count}/{len(phases_to_rebuild)} cards")
    if scores:
        avg_score = sum(scores) / len(scores)
        passed = sum(1 for s in scores if s >= REVIEW_PASS_THRESHOLD)
        _log(f"Average score: {avg_score:.1f}/100")
        _log(f"Passed: {passed}/{len(scores)} ({100*passed/len(scores):.0f}%)")
        _log(f"Total attempts: {total_attempts}")
    if error_count:
        _log(f"Errors: {error_count}")
        for pid, err in sorted(errors):
            _log(f"  [{pid:02d}]: {err[:80]}")

    return 0 if error_count == 0 else 1


def phase_batch(series_dir: Path, parallel: int = 1, batch_size: str = "full") -> int:
    """Full pipeline: init (if needed) + generate + render."""
    content_path = series_dir / "lots" / "lot_content.yml"

    if not content_path.exists():
        rc = phase_init(series_dir)
        if rc != 0:
            return rc

    rc = phase_generate(series_dir, parallel=parallel)
    if rc != 0:
        return rc

    return phase_render(series_dir, parallel=parallel, batch_size=batch_size)


def phase_export(series_dir: Path, target: str, card_type: str = "all") -> int:
    """Package cards for target platform.

    Args:
        series_dir: Path to series directory
        target: Platform name (playingcards, makeplayingcards, thegamecrafter)
        card_type: What to export - "cards", "lots", or "all" (default)
    """
    # Import from package
    try:
        from hypertext.lots.exporter import export_for_platform
    except ImportError:
        # Fallback to old location
        sys.path.insert(0, str(TOOLS_DIR))
        try:
            from lot_exporter import export_for_platform
        except ImportError as e:
            _log(f"Error importing lot_exporter: {e}")
            _log("Make sure lot_exporter.py exists in the tools directory.")
            return 1

    return export_for_platform(series_dir, target, card_type)


def main() -> int:
    _setup_interrupt_handler()
    parser = argparse.ArgumentParser(
        description="Lot (Phase Card) Generation Pipeline for Hypertext",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m hypertext.lots.generation --phase init --series series/2026-Q1
  python -m hypertext.lots.generation --phase generate --series series/2026-Q1
  python -m hypertext.lots.generation --phase render --series series/2026-Q1
  python -m hypertext.lots.generation --phase render --series series/2026-Q1 --review  # Grade & retry if <90%
  python -m hypertext.lots.generation --phase rebuild --series series/2026-Q1 --parallel 2  # Force re-render with grading
  python -m hypertext.lots.generation --phase batch --series series/2026-Q1
  python -m hypertext.lots.generation --phase export --series series/2026-Q1 --target playingcards
  python -m hypertext.lots.generation --phase grade --series series/2026-Q1 --parallel 2
"""
    )
    parser.add_argument(
        "--phase",
        required=True,
        choices=["init", "generate", "render", "rebuild", "batch", "export", "grade"],
        help="Pipeline phase to run"
    )
    parser.add_argument(
        "--series",
        required=True,
        help="Path to series directory (e.g., series/2026-Q1)"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Number of cards to render in parallel (default: 1)"
    )
    parser.add_argument(
        "--target",
        choices=["playingcards", "makeplayingcards", "thegamecrafter"],
        help="Export target platform (required for export phase)"
    )
    parser.add_argument(
        "--batch-size",
        choices=["single", "quarter", "half", "full"],
        default="full",
        help="How many lots to render: single (1), quarter (8), half (15), full (30, default)"
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help="Grade each card after rendering and re-render if score < 90%% (up to 3 attempts)"
    )
    parser.add_argument(
        "--export-type",
        choices=["cards", "lots", "all"],
        default="all",
        help="What to export: cards (main deck), lots (phase cards), or all (default)"
    )
    args = parser.parse_args()

    series_dir = Path(args.series)
    if not series_dir.exists():
        _log(f"Error: Series directory does not exist: {series_dir}")
        return 1

    batch_size = getattr(args, "batch_size", "full")

    if args.phase == "init":
        return phase_init(series_dir)
    elif args.phase == "generate":
        return phase_generate(series_dir, parallel=args.parallel)
    elif args.phase == "render":
        return phase_render(series_dir, parallel=args.parallel, batch_size=batch_size, review=args.review)
    elif args.phase == "rebuild":
        return phase_rebuild(series_dir, batch_size=batch_size, parallel=args.parallel)
    elif args.phase == "batch":
        return phase_batch(series_dir, parallel=args.parallel, batch_size=batch_size)
    elif args.phase == "export":
        if not args.target:
            _log("Error: --target required for export phase")
            return 2
        return phase_export(series_dir, args.target, args.export_type)
    elif args.phase == "grade":
        return phase_grade(series_dir, parallel=args.parallel)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
