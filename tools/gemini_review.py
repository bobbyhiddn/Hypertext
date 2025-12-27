#!/usr/bin/env python3
"""
Vision-based card review and scoring system.

Uses Gemini's vision API to evaluate generated cards against a quality checklist.
Returns a score out of 100 and detailed feedback for corrections.
"""
import base64
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    requests = None


@dataclass
class ReviewResult:
    """Result of a card review."""
    score: int  # 0-100
    passed: bool  # True if score >= threshold
    categories: dict[str, dict[str, Any]]  # Category -> {score, max, issues}
    corrections: list[str]  # List of specific corrections needed
    needs_rebuild: bool  # True if score < 90 (full rebuild needed)
    raw_response: str  # Raw model response for debugging


# Scoring rubric - 100 points total
REVIEW_RUBRIC = """
## CARD REVIEW RUBRIC (100 points total)

Score each category. Deduct points for issues found. Return JSON.

### 1. FORMATTING & STRUCTURE (35 points max)
- Card frame/border present and intact (5 pts) - deduct if frame broken, missing corners, or incomplete
- All required panels visible (10 pts) - need: Header, Art, Stats Row, Ability, OT Verse, NT Verse, Greek/Hebrew split, Trivia. Deduct 1-2 pts per missing panel
- Stat pips are circles only (5 pts) - deduct all if squares/stars/other shapes used
- Rarity icon matches rarity text (5 pts) - COMMON=white circle, UNCOMMON=green square, RARE=gold hexagon, GLORIOUS=orange diamond. Deduct if wrong shape/color
- Card number visible and formatted (5 pts) - should be 3 digits like "001"
- No duplicate headings/sections (5 pts) - deduct if any section header appears twice

### 2. TEXT CLARITY & ACCURACY (30 points max)
- Word/Title clearly readable (5 pts) - the main word at top must be crisp and legible
- Gloss clearly readable (5 pts) - subtitle/definition must be readable
- Ability text fully rendered (5 pts) - no cutoff, no missing words, complete sentence
- Verse references readable (5 pts) - both OT and NT verse lines must be legible
- Greek/Hebrew render correctly (5 pts) - Hebrew should be right-to-left, Greek should be proper glyphs
- No garbled/warped/broken text (5 pts) - deduct for any distorted, smeared, or illegible text anywhere

### 3. ART QUALITY (20 points max)
- Art matches the word/theme (8 pts) - the artwork should clearly relate to the card's word
- No text inside artwork (5 pts) - the art panel should be pure illustration, no letters/words
- Art fills panel appropriately (4 pts) - no awkward cropping, no excessive empty space
- Art style consistent (3 pts) - painterly, mythic realism, parchment-friendly tones

### 4. CONTENT ALIGNMENT (15 points max)
- Ability matches card flavor (5 pts) - the game ability should thematically connect to the word's meaning
- Trivia bullets present (5 pts) - should have 3-5 bullet points visible
- No visible brackets [ ] (5 pts) - deduct all 5 if any square brackets remain around text
"""

REVIEW_PROMPT_TEMPLATE = """You are a quality control reviewer for Hypertext trading cards.

Analyze this card image against the expected content and score it using the rubric.

## EXPECTED CARD CONTENT:
- Word: {word}
- Gloss: {gloss}
- Card Type: {card_type}
- Rarity: {rarity} (icon should be: {rarity_icon_desc})
- Card Number: {number}
- Ability: {ability}
- Stats: LORE={lore}, CONTEXT={context}, COMPLEXITY={complexity}

{rubric}

## YOUR TASK:
1. Examine the card image carefully
2. Score each category based on what you see
3. List specific issues found
4. Suggest specific corrections needed

## RESPONSE FORMAT (JSON only):
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

Return ONLY the JSON, no other text.
"""

RARITY_ICON_DESCRIPTIONS = {
    "COMMON": "white circle with navy outline",
    "UNCOMMON": "green square with navy outline",
    "RARE": "gold hexagon with navy outline",
    "GLORIOUS": "orange diamond (rhombus) with navy outline"
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


def _parse_review_response(text: str) -> dict:
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
        raise RuntimeError(f"Failed to parse review response as JSON: {e}\nResponse: {raw[:500]}")


def review_card(
    image_path: Path,
    card_json: dict,
    *,
    model: str | None = None,
    pass_threshold: int = 90,
    max_attempts: int = 3,
    base_delay_s: float = 2.0,
) -> ReviewResult:
    """
    Review a generated card image against expected content.

    Args:
        image_path: Path to the card image
        card_json: The card.json data with expected content
        model: Gemini model to use (default from env or gemini-3-pro-preview)
        pass_threshold: Minimum score to pass (default 90)
        max_attempts: Retry attempts on API failure
        base_delay_s: Base delay for exponential backoff

    Returns:
        ReviewResult with score, issues, and corrections
    """
    if requests is None:
        raise RuntimeError("requests library required. Install with: pip install requests")

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable required")

    model = model or os.environ.get("GEMINI_REVIEW_MODEL", "gemini-3-pro-preview")

    # Extract expected content from card.json
    content = card_json.get("content", {})
    word = content.get("WORD", "UNKNOWN")
    gloss = content.get("GLOSS", "")
    card_type = content.get("CARD_TYPE", "")
    rarity = content.get("RARITY_TEXT", "COMMON")
    number = content.get("NUMBER", "000")
    ability = content.get("ABILITY_TEXT", "")
    lore = content.get("STAT_LORE", 0)
    context = content.get("STAT_CONTEXT", 0)
    complexity = content.get("STAT_COMPLEXITY", 0)

    rarity_icon_desc = RARITY_ICON_DESCRIPTIONS.get(rarity, "unknown icon")

    # Build prompt
    prompt = REVIEW_PROMPT_TEMPLATE.format(
        word=word,
        gloss=gloss,
        card_type=card_type,
        rarity=rarity,
        rarity_icon_desc=rarity_icon_desc,
        number=number,
        ability=ability,
        lore=lore,
        context=context,
        complexity=complexity,
        rubric=REVIEW_RUBRIC,
    )

    # Encode image
    image_data = _encode_image(image_path)
    mime_type = _get_mime_type(image_path)

    # Build API request
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_data,
                        }
                    },
                    {"text": prompt},
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,  # Low temp for consistent scoring
            "maxOutputTokens": 2048,
        },
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }

    # Make request with retries
    last_error: Exception | None = None
    for attempt in range(max_attempts):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=120)

            if resp.status_code == 429:
                # Rate limited - use Retry-After or exponential backoff
                retry_after = int(resp.headers.get("Retry-After", base_delay_s * (2 ** attempt)))
                time.sleep(retry_after)
                continue

            resp.raise_for_status()

            data = resp.json()

            # Extract text from response
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError(f"No candidates in response: {data}")

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise RuntimeError(f"No parts in response: {data}")

            response_text = parts[0].get("text", "")
            if not response_text:
                raise RuntimeError(f"Empty text in response: {data}")

            # Parse the review
            review_data = _parse_review_response(response_text)

            # Build result
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
                passed=total_score >= pass_threshold,
                categories=categories,
                corrections=corrections,
                needs_rebuild=total_score < 90,
                raw_response=response_text,
            )

        except Exception as e:
            last_error = e
            if attempt < max_attempts - 1:
                time.sleep(base_delay_s * (2 ** attempt))

    raise RuntimeError(f"Review failed after {max_attempts} attempts: {last_error}")


def format_review_report(result: ReviewResult) -> str:
    """Format a review result as a human-readable report."""
    lines = [
        f"## Card Review Score: {result.score}/100",
        "",
        "### Category Breakdown:",
    ]

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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Review a Hypertext card image")
    parser.add_argument("image_path", help="Path to card image")
    parser.add_argument("card_json_path", help="Path to card.json")
    parser.add_argument("--threshold", type=int, default=90, help="Pass threshold (default 90)")

    args = parser.parse_args()

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
