#!/usr/bin/env python3
"""Multi-stage vision-based card review and scoring system.

Uses a two-stage approach:
1. DESCRIBE: LLM describes what it sees on the card image
2. SCORE: A separate call compares the description against the rubric

This separation ensures more accurate evaluation by forcing the model
to first observe, then judge.
"""

import argparse
import base64
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


@dataclass
class CardDescription:
    """Detailed description of what the LLM sees on the card."""
    card_number: str
    card_number_format: str  # e.g., "#003", "[#003]", "003"
    word: str
    gloss: str
    card_type: str
    type_icon_shape: str  # "book", "pencil", "sparkle_pencil", "quill", "crown", "none", etc.
    rarity_text: str
    rarity_icon_shape: str  # "diamond", "circle", "square", etc.
    rarity_icon_color: str  # "orange", "gold", "green", etc.
    stat_pip_shape: str  # "circle", "diamond", "square", etc.
    stat_pip_fill_color: str  # "navy", "gold", "blue", etc.
    stat_lore: int
    stat_context: int
    stat_complexity: int
    ability_text: str
    ot_verse_visible: bool
    nt_verse_visible: bool
    verse_label_style: str  # "centered_above", "side_boxes", "other"
    greek_text_visible: bool
    hebrew_text_visible: bool
    # Transliteration formatting (CRITICAL for style compliance)
    transliteration_position: str = "below"  # "below" (correct) or "beside" (wrong)
    transliteration_has_parentheses: bool = False  # True = wrong, should not have parentheses
    trivia_bullet_count: int
    has_brackets: bool
    bracket_locations: list[str]
    art_description: str
    text_inside_art: bool
    frame_intact: bool
    frame_corner_style: str  # "chamfered", "ornate_scrollwork", "rounded", "square", "other"
    all_panels_visible: bool
    missing_panels: list[str]
    garbled_text_locations: list[str]
    # Style match (CRITICAL for quality control)
    style_matches_reference: bool = True  # False = automatic fail
    style_mismatch_reason: str = ""
    raw_response: str = ""


@dataclass
class ReviewResult:
    """Result of a card review."""
    score: int  # 0-100
    passed: bool  # True if score >= threshold
    categories: dict[str, dict[str, Any]]  # Category -> {score, max, issues}
    corrections: list[str]  # List of specific corrections needed
    needs_rebuild: bool  # True if score < 90 (full rebuild needed)
    description: CardDescription | None = None  # The description from stage 1
    raw_response: str = ""  # Raw model response for debugging


# Stage 1: Description prompt - just observe, don't judge
DESCRIBE_PROMPT = """You are examining a Hypertext trading card image. Your job is to describe EXACTLY what you see.

Do NOT judge quality or correctness. Just report what is actually visible on the card.

## IDEAL CARD LAYOUT (what elements to look for)

A correctly formatted Hypertext card should have these elements:
- HEADER AREA: Card number (format: #XXX), card type label, main word/title, gloss/subtitle
- TYPE ICON: WHITE icon in navy circle (top-left): NOUN=book, VERB=pencil, ADJECTIVE=sparkle pencil, NAME=quill, TITLE=crown
- TOP RIGHT: Rarity text followed by a diamond-shaped icon
- ART PANEL: Large illustration in the middle, no text inside the art
- STATS ROW: Three stats (LORE, CONTEXT, COMPLEXITY) each with 5 small circle-shaped pips
  - Filled pips should be NAVY (dark blue) color
  - Empty pips should be outlined/hollow
- ABILITY PANEL: One line of game ability text
- VERSE PANELS: OT verse reference and snippet, NT verse reference and snippet
- GREEK/HEBREW STRIP: Greek text on one side, Hebrew text on other, with transliterations BELOW (not beside) each script, NO PARENTHESES around transliterations
- TRIVIA SECTION: 3-5 bullet points of biblical trivia
- FOOTER: Series identifier
- FRAME: Navy border with gold trim, no brackets [ ] anywhere

## WHAT TO EXAMINE AND REPORT

1. CARD NUMBER: What text appears in the card number area? Report the EXACT format you see (e.g., "#003" vs "[#003]" vs "003" vs "#003 NOUN")
2. WORD/TITLE: What is the main word/title at the top?
3. GLOSS: What is the subtitle/definition text?
4. CARD TYPE: What type label is shown (NOUN, VERB, etc.)?
5. TYPE ICON: What icon is in the top-left navy circle? (book/pencil/sparkle_pencil/quill/crown/none/other)
6. RARITY: What rarity text is shown? What SHAPE is the rarity icon (circle/square/diamond/hexagon)? What COLOR is it?
7. STAT PIPS:
   - What SHAPE are the stat pips? (circles/diamonds/squares/stars)
   - What COLOR are the FILLED pips? (navy/dark blue/gold/yellow/other - be specific)
   - Count filled pips for each stat (Lore, Context, Complexity)
8. ABILITY TEXT: What does the ability text say?
9. VERSES: Is the OT verse section visible and readable? Is the NT verse section visible and readable?
10. GREEK/HEBREW: Is Greek text visible? Is Hebrew text visible? Are transliterations shown?
   - TRANSLITERATION POSITION: Are transliterations positioned BELOW their respective scripts (correct) or BESIDE/NEXT TO them (wrong)?
   - TRANSLITERATION PARENTHESES: Are transliterations wrapped in parentheses (wrong) or shown without parentheses (correct)?
11. TRIVIA: How many trivia bullet points are visible?
12. BRACKETS: Are there any square brackets [ ] visible ANYWHERE on the card? If yes, list exact locations.
13. ART PANEL: Briefly describe the artwork. Is there any TEXT inside the art panel?
14. FRAME: Is the card frame/border intact and complete?
15. PANELS: Are all expected panels visible? List any missing sections.
16. TEXT QUALITY: Is any text garbled, warped, or illegible? Where?

Return ONLY JSON in this exact format:
```json
{
  "card_number": "<exact text shown, e.g., '#003 NOUN' or '[#003]'>",
  "card_number_format": "<just the number format: '#003' or '[#003]' or '003'>",
  "word": "<main word>",
  "gloss": "<subtitle text>",
  "card_type": "<type shown>",
  "type_icon_shape": "<book|pencil|sparkle_pencil|quill|crown|none|other>",
  "rarity_text": "<rarity word>",
  "rarity_icon_shape": "<circle|square|diamond|hexagon|other>",
  "rarity_icon_color": "<color name>",
  "stat_pip_shape": "<circle|diamond|square|star|other>",
  "stat_pip_fill_color": "<navy|dark blue|gold|yellow|blue|other - be specific>",
  "stat_lore": <number of filled pips 0-5>,
  "stat_context": <number of filled pips 0-5>,
  "stat_complexity": <number of filled pips 0-5>,
  "ability_text": "<ability text>",
  "ot_verse_visible": true|false,
  "nt_verse_visible": true|false,
  "greek_text_visible": true|false,
  "hebrew_text_visible": true|false,
  "transliteration_position": "<below|beside>",
  "transliteration_has_parentheses": true|false,
  "trivia_bullet_count": <number>,
  "has_brackets": true|false,
  "bracket_locations": ["location1", "location2"],
  "art_description": "<brief description>",
  "text_inside_art": true|false,
  "frame_intact": true|false,
  "all_panels_visible": true|false,
  "missing_panels": ["panel1", "panel2"],
  "garbled_text_locations": ["location1", "location2"],
  "style_matches_reference": true|false,
  "style_mismatch_reason": "<if false, explain differences from references>"
}
```
"""

# Prompt to analyze style reference images and build a rubric
DESCRIBE_STYLE_REFS_PROMPT = """You are provided {ref_count} Hypertext trading card reference images:
{image_labels}

Examine each image and describe the EXACT visual style that defines a correctly rendered Hypertext card.

Describe in detail:

1. FRAME/BORDER: What is the border style? (straight edges, rounded corners, ornate decorations?) What colors?

2. HEADER AREA: How is the card number formatted? Where is it positioned? What about the card type label?

3. TITLE SECTION: How is the main word/title styled? Font style? Size? Position?

4. RARITY DISPLAY: What shape is the rarity icon? (diamond, circle, square?) What position?

5. ART PANEL: What style is the artwork? How is it framed? Any decorative borders?

6. STAT PIPS: What SHAPE are the stat pips? (circles, diamonds, squares?) What COLOR are filled pips?

7. VERSE SECTIONS: How are OT and NT verse sections styled? Headers? Text alignment? Background colors?

8. TRIVIA SECTION: How are the bullet points formatted? What styling?

9. GREEK/HEBREW STRIP: Where is it positioned? How is it styled?

10. FOOTER: What appears at the bottom? What styling?

11. COLOR SCHEME: What are the primary colors used throughout? Navy? Gold? Parchment?

Be EXTREMELY SPECIFIC about visual details - this will be used to grade other cards for style consistency.
Any card that differs in these structural/style elements is a STYLE MISMATCH and must FAIL."""


# Stage 1b: Description prompt WITH style reference comparison
# Used when style reference images are provided for comparison
DESCRIBE_WITH_REFS_PROMPT = """You are a STRICT quality control inspector. Your job is to REJECT cards that don't match the reference style.

## STYLE RUBRIC (the AUTHORITATIVE reference for what cards MUST look like):
{style_rubric}

## IMAGES PROVIDED
{image_labels}

## YOUR TASK: FIND STYLE DIFFERENCES

Compare the TEST CARD (image [{test_idx}]) against the REFERENCE images. Look for ANY visual differences.

### CRITICAL STYLE CHECKS - IN ORDER OF IMPORTANCE:

**#1 BORDER/FRAME STYLE (MOST IMPORTANT):**
- CORRECT style has: SIMPLE STRAIGHT borders with CHAMFERED (diagonally cut) corners
- WRONG styles include: ornate/decorative borders, scrollwork, curved flourishes, rounded corners
- If the border looks "fancy" or "decorative" compared to references = AUTOMATIC FAIL
- The references have PLAIN, SIMPLE, STRAIGHT-EDGED frames

**#2 VERSE SECTION LAYOUT:**
- CORRECT: "OT VERSE" and "NT VERSE" text is CENTERED ABOVE the verse content
- WRONG: Labels in dark boxes/pills on the LEFT SIDE of the text
- If verse labels are positioned differently than references = STYLE MISMATCH

**#3 STAT PIP SHAPE:** Must be CIRCLES (not diamonds, squares, stars)

**#4 TYPE ICON (TOP-LEFT CIRCLE):**
- CORRECT: WHITE icon inside navy circle in top-left corner
- Icons by type: NOUN=book, VERB=pencil, ADJECTIVE=sparkle pencil (pencil with stars), NAME=quill, TITLE=crown
- WRONG: Missing icon, wrong icon for type, or icon not matching references

**#5 TRANSLITERATION FORMATTING (CRITICAL):**
- CORRECT: Transliterations appear BELOW their respective scripts (Greek/Hebrew) in smaller text
- WRONG: Transliterations appear BESIDE/NEXT TO the original script on the same line
- CORRECT: Transliterations shown WITHOUT parentheses (just the word, e.g., "logos")
- WRONG: Transliterations wrapped in parentheses (e.g., "(logos)")
- If transliteration is beside instead of below = STYLE MISMATCH
- If transliteration has parentheses = STYLE MISMATCH

**#6 OVERALL AESTHETIC:** Does the card look like it belongs with the references, or does it look like a DIFFERENT card game entirely?

### HOW TO DECIDE:
1. Look at the BORDER of each reference card - note how simple/plain it is
2. Look at the BORDER of the test card - is it equally simple, or more decorative?
3. If the test card has MORE decoration, flourishes, or ornate elements = FAIL
4. When in doubt, REJECT the card (false negatives are better than false positives)

## WHAT TO REPORT

Describe the TEST CARD:
1. CARD NUMBER: Exact format
2. WORD/TITLE: Main word
3. GLOSS: Subtitle
4. CARD TYPE: Type label
5. RARITY: Text and icon
6. STAT PIPS: Shape, color, counts
7. ABILITY TEXT: Full text
8. VERSE LAYOUT: Are labels CENTERED ABOVE text or IN SIDE BOXES?
9. GREEK/HEBREW: Visible?
   - TRANSLITERATION POSITION: below (correct) or beside (wrong)?
   - TRANSLITERATION PARENTHESES: none (correct) or has parentheses (wrong)?
10. TRIVIA: Bullet count
11. BRACKETS: Any [ ] visible?
12. ART: Brief description
13. FRAME/BORDER: Is it SIMPLE/STRAIGHT or ORNATE/DECORATIVE? Describe the corners.
14. STYLE VERDICT: PASS only if it matches references. FAIL if ANY structural difference.

Return ONLY JSON in this exact format:
```json
{{
  "card_number": "<exact text shown>",
  "card_number_format": "<just the number format: '#003' or '[#003]' or '003'>",
  "word": "<main word>",
  "gloss": "<subtitle text>",
  "card_type": "<type shown>",
  "type_icon_shape": "<book|pencil|sparkle_pencil|quill|crown|none|other>",
  "rarity_text": "<rarity word>",
  "rarity_icon_shape": "<circle|square|diamond|hexagon|other>",
  "rarity_icon_color": "<color name>",
  "stat_pip_shape": "<circle|diamond|square|star|other>",
  "stat_pip_fill_color": "<navy|dark blue|gold|yellow|blue|other>",
  "stat_lore": <number of filled pips 0-5>,
  "stat_context": <number of filled pips 0-5>,
  "stat_complexity": <number of filled pips 0-5>,
  "ability_text": "<ability text>",
  "ot_verse_visible": true|false,
  "nt_verse_visible": true|false,
  "verse_label_style": "<centered_above|side_boxes|other>",
  "greek_text_visible": true|false,
  "hebrew_text_visible": true|false,
  "transliteration_position": "<below|beside>",
  "transliteration_has_parentheses": true|false,
  "trivia_bullet_count": <number>,
  "has_brackets": true|false,
  "bracket_locations": ["location1", "location2"],
  "art_description": "<brief description>",
  "text_inside_art": true|false,
  "frame_intact": true|false,
  "frame_corner_style": "<chamfered|ornate_scrollwork|rounded|square|other>",
  "all_panels_visible": true|false,
  "missing_panels": ["panel1", "panel2"],
  "garbled_text_locations": ["location1", "location2"],
  "style_matches_reference": true|false,
  "style_mismatch_reason": "<if false, explain ALL structural differences from references>"
}}
```
"""

# Stage 2: Scoring prompt - compare description against expected content
SCORE_PROMPT_TEMPLATE = """You are scoring a trading card based on a description of what was observed.

## EXPECTED CONTENT:
- Card Number: #{number} (format must be #XXX, not [#XXX] or XXX)
- Word: {word}
- Gloss: {gloss}
- Card Type: {card_type}
- Rarity: {rarity} (icon should be a DIAMOND shape, {rarity_color} colored)
- Stats: LORE={lore}, CONTEXT={context}, COMPLEXITY={complexity}
- Stat pips must be CIRCLES with NAVY fill (not gold, not diamonds)
- Ability: {ability}

## OBSERVED DESCRIPTION:
{description_json}

## SCORING RUBRIC (100 points total):

### 1. FORMATTING & STRUCTURE (35 points max)
- Card frame intact (5 pts) - deduct if frame broken or incomplete
- All panels visible (10 pts) - deduct 2 pts per missing panel
- Stat pips are CIRCLES (5 pts) - deduct ALL 5 if not circles
- Stat pips are NAVY filled (5 pts) - deduct ALL 5 if gold/yellow/other color
- Rarity icon is DIAMOND shape (5 pts) - deduct all if wrong shape
- Card number format is #XXX (5 pts) - deduct all if brackets [#XXX] or missing hash

### 2. TEXT CLARITY & ACCURACY (30 points max)
- Word/title matches expected (5 pts)
- Gloss matches expected (5 pts)
- Ability text complete and correct (5 pts)
- Verses visible (5 pts)
- Greek/Hebrew visible (5 pts)
- No garbled/warped text (5 pts) - deduct for any illegible text

### 3. ART QUALITY (20 points max)
- Art present and fills panel (8 pts)
- No text inside artwork (5 pts) - deduct all if text in art
- Art style appropriate (4 pts)
- Art relates to word theme (3 pts)

### 4. CONTENT ALIGNMENT (15 points max)
- Stat pip counts match expected (5 pts)
- Trivia bullets present (5 pts) - should have 3-5
- No brackets [ ] anywhere (5 pts) - deduct ALL if any brackets visible

## YOUR TASK:
1. Compare the observed description against expected content
2. Score each category based on the rubric
3. List specific issues found
4. Provide specific corrections needed (be actionable)

Return ONLY JSON:
```json
{{
  "formatting": {{
    "score": <0-35>,
    "max": 35,
    "issues": ["issue1", "issue2"]
  }},
  "text_clarity": {{
    "score": <0-30>,
    "max": 30,
    "issues": ["issue1", "issue2"]
  }},
  "art_quality": {{
    "score": <0-20>,
    "max": 20,
    "issues": ["issue1", "issue2"]
  }},
  "content_alignment": {{
    "score": <0-15>,
    "max": 15,
    "issues": ["issue1", "issue2"]
  }},
  "total_score": <0-100>,
  "corrections": [
    "Specific correction 1",
    "Specific correction 2"
  ]
}}
```
"""

RARITY_COLORS = {
    "COMMON": "white",
    "UNCOMMON": "green",
    "RARE": "gold",
    "GLORIOUS": "orange"
}


def _encode_image(image_path: Path) -> str:
    """Read and base64 encode an image file."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def _get_mime_type(image_path: Path) -> str:
    """Get MIME type from file extension."""
    ext = image_path.suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(ext, "image/png")


def _parse_json_response(text: str) -> dict:
    """Parse JSON response from model, handling markdown fences."""
    raw = text.strip()

    # Try to extract from markdown code fence
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                try:
                    return json.loads(part)
                except json.JSONDecodeError:
                    continue

    # Try direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse response as JSON: {e}\nResponse: {raw[:500]}")


def _image_part_from_path(image_path: Path):
    """Create an image part from a file path using the SDK."""
    if types is None:
        raise RuntimeError("google-genai package required. Install with: pip install google-genai")

    with open(image_path, "rb") as f:
        img_bytes = f.read()
    mime_type = _get_mime_type(image_path)

    image_part = None
    if hasattr(types.Part, "from_bytes"):
        try:
            image_part = types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
        except Exception:
            pass

    if image_part is None and hasattr(types.Part, "from_image"):
        try:
            image_part = types.Part.from_image(image=img_bytes, mime_type=mime_type)
        except Exception:
            pass

    if image_part is None:
        try:
            blob_cls = getattr(types, "Blob", None)
            if blob_cls:
                image_part = types.Part(inline_data=blob_cls(data=img_bytes, mime_type=mime_type))
            else:
                image_part = types.Part(inline_data={"mime_type": mime_type, "data": img_bytes})
        except Exception as e:
            raise RuntimeError(f"Failed to construct image part: {e}")

    return image_part


def _call_gemini(
    prompt: str,
    *,
    image_path: Path | None = None,
    image_paths: list[Path] | None = None,
    model: str = "gemini-3-pro-preview",
    max_attempts: int = 3,
    base_delay_s: float = 2.0,
) -> str:
    """Make a Gemini API call using the SDK, optionally with image(s).

    Args:
        prompt: Text prompt to send
        image_path: Single image path (for backwards compatibility)
        image_paths: List of image paths (for multi-image comparison)
        model: Model to use
        max_attempts: Number of retry attempts
        base_delay_s: Base delay for exponential backoff
    """
    if genai is None:
        raise RuntimeError("google-genai package required. Install with: pip install google-genai")

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable required")

    client = genai.Client(api_key=api_key)

    contents = []
    # Handle multiple images first (for reference comparison)
    if image_paths:
        for img_path in image_paths:
            contents.append(_image_part_from_path(img_path))
    elif image_path:
        contents.append(_image_part_from_path(image_path))
    contents.append(types.Part.from_text(text=prompt))

    config = types.GenerateContentConfig(
        temperature=0.1,
        max_output_tokens=8192,
    )

    last_error: Exception | None = None
    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

            if not response.candidates:
                raise RuntimeError("No candidates in response")

            candidate = response.candidates[0]
            parts = candidate.content.parts if candidate.content else []

            if not parts:
                raise RuntimeError("No parts in response")

            response_text = parts[0].text if hasattr(parts[0], "text") else ""
            if not response_text:
                raise RuntimeError("Empty text in response")

            return response_text

        except Exception as e:
            last_error = e
            if attempt < max_attempts - 1:
                time.sleep(base_delay_s * (2 ** attempt))

    raise RuntimeError(f"API call failed after {max_attempts} attempts: {last_error}")


def describe_card_style_references(
    style_refs: list[str | Path],
    *,
    model: str | None = None,
) -> str:
    """Analyze style reference images to build a grading rubric.

    Like lot grading - first describes what correct cards look like,
    then uses this description when grading test cards.

    Args:
        style_refs: List of reference image paths
        model: Gemini model to use

    Returns:
        Text description of what a correct Hypertext card looks like
    """
    model = model or os.environ.get("GEMINI_REVIEW_MODEL", "gemini-3-pro-preview")

    if not style_refs:
        return "No style references provided."

    # Build image paths and labels
    image_paths = []
    labels = []
    for i, ref_path in enumerate(style_refs, 1):
        ref_p = Path(ref_path)
        if ref_p.exists():
            image_paths.append(ref_p)
            if "template" in str(ref_p).lower():
                labels.append(f"[{i}] TEMPLATE: {ref_p.name}")
            else:
                labels.append(f"[{i}] REFERENCE CARD: {ref_p.name}")

    if not image_paths:
        return "No valid style reference images found."

    prompt = DESCRIBE_STYLE_REFS_PROMPT.format(
        ref_count=len(image_paths),
        image_labels="\n".join(labels),
    )

    try:
        response_text = _call_gemini(
            prompt,
            image_paths=image_paths,
            model=model,
        )
        return response_text
    except Exception as e:
        return f"Error analyzing style references: {e}"


def describe_card(
    image_path: Path,
    *,
    style_refs: list[str | Path] | None = None,
    style_rubric: str | None = None,
    model: str | None = None,
) -> CardDescription:
    """Stage 1: Have the LLM describe what it sees on the card.

    This is a pure observation step - no judgment or scoring.
    When style_refs are provided, also checks if card matches reference style.

    Args:
        image_path: Path to the card image to describe
        style_refs: Optional list of reference image paths for style comparison
        style_rubric: Optional pre-generated description of correct style (from describe_card_style_references)
        model: Gemini model to use
    """
    model = model or os.environ.get("GEMINI_REVIEW_MODEL", "gemini-3-pro-preview")

    if style_refs:
        # Build image list: refs first, then test card
        image_paths = []
        labels = []

        for i, ref_path in enumerate(style_refs, 1):
            ref_p = Path(ref_path)
            if ref_p.exists():
                image_paths.append(ref_p)
                labels.append(f"[{i}] REFERENCE: {ref_p.name}")

        # Add the test card
        test_idx = len(image_paths) + 1
        image_paths.append(Path(image_path))
        labels.append(f"[{test_idx}] TEST CARD: {Path(image_path).name}")

        # Use the reference comparison prompt with style rubric
        ref_count = len(style_refs)
        rubric_text = style_rubric or "No pre-analyzed rubric available. Compare visually to reference images."
        prompt = DESCRIBE_WITH_REFS_PROMPT.format(
            style_rubric=rubric_text,
            image_labels="\n".join(labels),
            ref_count=ref_count if ref_count > 0 else 1,
            test_idx=test_idx,
        )

        response_text = _call_gemini(
            prompt,
            image_paths=image_paths,
            model=model,
        )
    else:
        # No refs, use simple describe prompt
        response_text = _call_gemini(
            DESCRIBE_PROMPT,
            image_path=image_path,
            model=model,
        )

    data = _parse_json_response(response_text)

    # Check for automatic style mismatch based on specific fields
    verse_style = data.get("verse_label_style", "centered_above")
    frame_corners = data.get("frame_corner_style", "chamfered").lower()

    # If verse labels are in side boxes, that's an automatic style mismatch
    explicit_mismatch = data.get("style_matches_reference", True)
    auto_mismatch_reasons = []

    if verse_style == "side_boxes":
        auto_mismatch_reasons.append("Verse labels are in side boxes instead of centered above")
        explicit_mismatch = False

    # Any non-chamfered frame style is a mismatch
    bad_frame_styles = ["ornate", "scrollwork", "ornate_scrollwork", "decorative", "rounded", "curved", "fancy", "flourish", "other"]
    if any(bad in frame_corners for bad in bad_frame_styles):
        auto_mismatch_reasons.append(f"Frame style is '{frame_corners}' - must be simple/chamfered")
        explicit_mismatch = False
    elif frame_corners not in ["chamfered", "simple", "straight", "diagonal"]:
        # Unknown style - flag it
        auto_mismatch_reasons.append(f"Frame style '{frame_corners}' doesn't match reference (expected chamfered)")
        explicit_mismatch = False

    # Transliteration formatting validation
    translit_position = data.get("transliteration_position", "below").lower()
    translit_has_parens = data.get("transliteration_has_parentheses", False)

    if translit_position == "beside":
        auto_mismatch_reasons.append("Transliterations are beside/next to the original script - must be BELOW")
        explicit_mismatch = False

    if translit_has_parens:
        auto_mismatch_reasons.append("Transliterations are wrapped in parentheses - must NOT have parentheses")
        explicit_mismatch = False

    # Type icon validation - check if icon matches expected for card type
    type_icon = data.get("type_icon_shape", "").lower()
    card_type = data.get("card_type", "").upper()
    expected_icons = {
        "NOUN": ["book", "closed_book", "closed book"],
        "VERB": ["pencil"],
        "ADJECTIVE": ["sparkle_pencil", "sparkle pencil", "pencil_stars", "pencil with stars"],
        "NAME": ["quill", "feather", "feather_quill", "feather quill"],
        "TITLE": ["crown"],
    }
    if card_type in expected_icons:
        valid_icons = expected_icons[card_type]
        if type_icon and type_icon not in ["none", "other", ""] and not any(valid in type_icon for valid in valid_icons):
            auto_mismatch_reasons.append(f"Type icon '{type_icon}' doesn't match {card_type} (expected: {valid_icons[0]})")
            explicit_mismatch = False
        elif type_icon in ["none", ""]:
            auto_mismatch_reasons.append(f"Missing type icon for {card_type} - should be {valid_icons[0]}")
            explicit_mismatch = False

    # Combine mismatch reasons
    mismatch_reason = data.get("style_mismatch_reason", "")
    if auto_mismatch_reasons:
        if mismatch_reason:
            mismatch_reason = mismatch_reason + "; " + "; ".join(auto_mismatch_reasons)
        else:
            mismatch_reason = "; ".join(auto_mismatch_reasons)

    return CardDescription(
        card_number=data.get("card_number", ""),
        card_number_format=data.get("card_number_format", ""),
        word=data.get("word", ""),
        gloss=data.get("gloss", ""),
        card_type=data.get("card_type", ""),
        type_icon_shape=data.get("type_icon_shape", ""),
        rarity_text=data.get("rarity_text", ""),
        rarity_icon_shape=data.get("rarity_icon_shape", ""),
        rarity_icon_color=data.get("rarity_icon_color", ""),
        stat_pip_shape=data.get("stat_pip_shape", ""),
        stat_pip_fill_color=data.get("stat_pip_fill_color", ""),
        stat_lore=data.get("stat_lore", 0),
        stat_context=data.get("stat_context", 0),
        stat_complexity=data.get("stat_complexity", 0),
        ability_text=data.get("ability_text", ""),
        ot_verse_visible=data.get("ot_verse_visible", False),
        nt_verse_visible=data.get("nt_verse_visible", False),
        verse_label_style=verse_style,
        greek_text_visible=data.get("greek_text_visible", False),
        hebrew_text_visible=data.get("hebrew_text_visible", False),
        transliteration_position=translit_position,
        transliteration_has_parentheses=translit_has_parens,
        trivia_bullet_count=data.get("trivia_bullet_count", 0),
        has_brackets=data.get("has_brackets", False),
        bracket_locations=data.get("bracket_locations", []),
        art_description=data.get("art_description", ""),
        text_inside_art=data.get("text_inside_art", False),
        frame_intact=data.get("frame_intact", True),
        frame_corner_style=frame_corners,
        all_panels_visible=data.get("all_panels_visible", True),
        missing_panels=data.get("missing_panels", []),
        garbled_text_locations=data.get("garbled_text_locations", []),
        style_matches_reference=explicit_mismatch,
        style_mismatch_reason=mismatch_reason,
        raw_response=response_text,
    )


def score_against_rubric(
    description: CardDescription,
    card_json: dict,
    *,
    model: str | None = None,
) -> ReviewResult:
    """Stage 2: Score the description against the expected content and rubric.

    This is a pure judgment step - comparing observations to expectations.
    """
    model = model or os.environ.get("GEMINI_REVIEW_MODEL", "gemini-3-pro-preview")

    # Extract expected content
    content = card_json.get("content", {})
    word = content.get("WORD", "UNKNOWN")
    gloss = content.get("GLOSS", "")
    card_type = content.get("CARD_TYPE", "")
    rarity = content.get("RARITY_TEXT", "COMMON")
    number = content.get("NUMBER", "000")
    ability = content.get("ABILITY_TEXT", "")
    lore = content.get("STAT_LORE", 0)
    context_stat = content.get("STAT_CONTEXT", 0)
    complexity = content.get("STAT_COMPLEXITY", 0)

    rarity_color = RARITY_COLORS.get(rarity, "white")

    # Convert description to JSON for the prompt
    description_dict = {
        "card_number": description.card_number,
        "card_number_format": description.card_number_format,
        "word": description.word,
        "gloss": description.gloss,
        "card_type": description.card_type,
        "type_icon_shape": description.type_icon_shape,
        "rarity_text": description.rarity_text,
        "rarity_icon_shape": description.rarity_icon_shape,
        "rarity_icon_color": description.rarity_icon_color,
        "stat_pip_shape": description.stat_pip_shape,
        "stat_pip_fill_color": description.stat_pip_fill_color,
        "stat_lore": description.stat_lore,
        "stat_context": description.stat_context,
        "stat_complexity": description.stat_complexity,
        "ability_text": description.ability_text,
        "ot_verse_visible": description.ot_verse_visible,
        "nt_verse_visible": description.nt_verse_visible,
        "greek_text_visible": description.greek_text_visible,
        "hebrew_text_visible": description.hebrew_text_visible,
        "trivia_bullet_count": description.trivia_bullet_count,
        "has_brackets": description.has_brackets,
        "bracket_locations": description.bracket_locations,
        "art_description": description.art_description,
        "text_inside_art": description.text_inside_art,
        "frame_intact": description.frame_intact,
        "all_panels_visible": description.all_panels_visible,
        "missing_panels": description.missing_panels,
        "garbled_text_locations": description.garbled_text_locations,
    }

    prompt = SCORE_PROMPT_TEMPLATE.format(
        number=number,
        word=word,
        gloss=gloss,
        card_type=card_type,
        rarity=rarity,
        rarity_color=rarity_color,
        lore=lore,
        context=context_stat,
        complexity=complexity,
        ability=ability,
        description_json=json.dumps(description_dict, indent=2),
    )

    response_text = _call_gemini(prompt, model=model)
    review_data = _parse_json_response(response_text)

    total_score = review_data.get("total_score", 0)

    categories = {
        "formatting": review_data.get("formatting", {"score": 0, "max": 35, "issues": []}),
        "text_clarity": review_data.get("text_clarity", {"score": 0, "max": 30, "issues": []}),
        "art_quality": review_data.get("art_quality", {"score": 0, "max": 20, "issues": []}),
        "content_alignment": review_data.get("content_alignment", {"score": 0, "max": 15, "issues": []}),
    }

    corrections = review_data.get("corrections", [])

    return ReviewResult(
        score=total_score,
        passed=total_score >= 90,
        categories=categories,
        corrections=corrections,
        needs_rebuild=total_score < 90,
        description=description,
        raw_response=response_text,
    )


def review_card(
    image_path: Path,
    card_json: dict,
    *,
    model: str | None = None,
    pass_threshold: int = 90,
    max_attempts: int = 3,
    base_delay_s: float = 2.0,
) -> ReviewResult:
    """Full two-stage review of a card image.

    Stage 1: Describe what's on the card (observation only)
    Stage 2: Score the description against the rubric (judgment)

    This separation ensures more accurate evaluation.
    """
    model = model or os.environ.get("GEMINI_REVIEW_MODEL", "gemini-3-pro-preview")

    # Stage 1: Describe
    description = describe_card(image_path, model=model)

    # Stage 2: Score
    result = score_against_rubric(description, card_json, model=model)
    result.passed = result.score >= pass_threshold

    return result


def format_description_report(description: CardDescription) -> str:
    """Format a card description as a human-readable report."""
    lines = [
        "## Card Description (What the LLM Sees)",
        "",
        f"**Card Number:** {description.card_number} (format: {description.card_number_format})",
        f"**Word:** {description.word}",
        f"**Gloss:** {description.gloss}",
        f"**Type:** {description.card_type}",
        f"**Rarity:** {description.rarity_text} ({description.rarity_icon_shape} icon, {description.rarity_icon_color})",
        "",
        "### Stats",
        f"- Pip Shape: {description.stat_pip_shape}",
        f"- Pip Fill Color: {description.stat_pip_fill_color}",
        f"- Lore: {description.stat_lore}/5",
        f"- Context: {description.stat_context}/5",
        f"- Complexity: {description.stat_complexity}/5",
        "",
        "### Content Visibility",
        f"- OT Verse: {'✓' if description.ot_verse_visible else '✗'}",
        f"- NT Verse: {'✓' if description.nt_verse_visible else '✗'}",
        f"- Greek: {'✓' if description.greek_text_visible else '✗'}",
        f"- Hebrew: {'✓' if description.hebrew_text_visible else '✗'}",
        f"- Transliteration position: {description.transliteration_position} {'✓' if description.transliteration_position == 'below' else '✗ (should be below)'}",
        f"- Transliteration parentheses: {'✗ YES (wrong)' if description.transliteration_has_parentheses else '✓ None (correct)'}",
        f"- Trivia bullets: {description.trivia_bullet_count}",
        "",
        "### Issues Detected",
        f"- Brackets visible: {'YES - ' + ', '.join(description.bracket_locations) if description.has_brackets else 'No'}",
        f"- Text in art: {'YES' if description.text_inside_art else 'No'}",
        f"- Frame intact: {'Yes' if description.frame_intact else 'NO - damaged'}",
        f"- Missing panels: {', '.join(description.missing_panels) if description.missing_panels else 'None'}",
        f"- Garbled text: {', '.join(description.garbled_text_locations) if description.garbled_text_locations else 'None'}",
        "",
        "### Art Description",
        f"{description.art_description}",
    ]
    return "\n".join(lines)


def format_review_report(result: ReviewResult) -> str:
    """Format a review result as a human-readable report."""
    lines = []

    # Include description if available
    if result.description:
        lines.append(format_description_report(result.description))
        lines.extend(["", "---", ""])

    lines.extend([
        f"## Card Review Score: {result.score}/100",
        "",
        "### Category Breakdown:",
    ])

    for name, data in result.categories.items():
        score = data.get("score", 0)
        max_score = data.get("max", 0)
        issues = data.get("issues", [])

        status = "✓" if score == max_score else "⚠" if score >= max_score * 0.7 else "✗"
        lines.append(f"- {status} {name.replace('_', ' ').title()}: {score}/{max_score}")

        for issue in issues:
            lines.append(f"  - {issue}")

    if result.corrections:
        lines.extend(["", "### Corrections Needed:"])
        for i, correction in enumerate(result.corrections, 1):
            lines.append(f"{i}. {correction}")

    lines.extend([
        "",
        f"**Status:** {'PASS' if result.passed else 'NEEDS REBUILD' if result.needs_rebuild else 'NEEDS REVISION'}",
    ])

    return "\n".join(lines)


def describe_palette(image_path: Path, model: str | None = None) -> str:
    """Describe symbols/icons in a palette image without card-specific assumptions.

    Args:
        image_path: Path to the palette image
        model: Optional model override

    Returns:
        Text description of each symbol in the palette
    """
    if genai is None:
        raise ImportError("google-genai package required")

    client = genai.Client()
    model_name = model or os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    prompt = """Describe each symbol/icon in this image in detail.

For each distinct symbol you see:
1. Identify its position (left to right, or row/column if arranged in a grid)
2. Describe the exact visual appearance - shapes, lines, elements
3. What object or concept it represents
4. Any distinguishing features that make it unique

Be specific and precise about visual details. These descriptions will be used as a reference rubric for recreating the symbols accurately."""

    response = client.models.generate_content(
        model=model_name,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            prompt,
        ],
    )

    return response.text


def main() -> int:
    """CLI entrypoint for card review."""
    parser = argparse.ArgumentParser(description="Review a Hypertext card image (two-stage)")
    parser.add_argument("image_path", help="Path to card image")
    parser.add_argument("card_json_path", nargs="?", help="Path to card.json (optional for --describe-only)")
    parser.add_argument("--threshold", type=int, default=90, help="Pass threshold (default 90)")
    parser.add_argument("--describe-only", action="store_true", help="Only run description stage")
    parser.add_argument("--describe-palette", action="store_true", help="Describe symbols in a palette image")

    args = parser.parse_args()

    if args.describe_palette:
        description = describe_palette(Path(args.image_path))
        print(description)
        return 0
    elif args.describe_only:
        description = describe_card(Path(args.image_path))
        print(format_description_report(description))
    else:
        if not args.card_json_path:
            print("ERROR: card_json_path is required for full review (use --describe-only for description only)")
            return 1

        with open(args.card_json_path, "r", encoding="utf-8") as f:
            card_data = json.load(f)

        result = review_card(
            Path(args.image_path),
            card_data,
            pass_threshold=args.threshold,
        )

        print(format_review_report(result))
        print(f"\nRaw score: {result.score}")

        import sys
        sys.exit(0 if result.passed else 1)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
