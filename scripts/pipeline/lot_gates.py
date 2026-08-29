"""Content and icon gates for a rendered Lot face.

Carried over from the card pipeline, which never trusts a re-render on style alone:
`check_ability_text` transcribes the printed copy and compares it to the record, and
`detect_placeholder_leaks` hunts template strings with a reference-free query. The Lot
pipeline had neither, which is how a face shipped with a placeholder verse line, a
garbled wreath line and the wrong Portion value.

Two gates:
  ICONS   - two-sided. A type icon must sit inside the band the rest of the set uses,
            so a glyph that is too FILLED (the original defect) and one that is too
            LIGHT (a thinner third variant) are both rejected.
  CONTENT - Gemini transcribes the printed fields and they must match the rules record.

A pixel-drift gate is deliberately NOT used: an image model re-renders rather than
edits, so two renders of identical content differ as much as two unrelated lots.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image
from hypertext.gemini.review import _call_gemini, _parse_json_response

X0, X1, ITOP, IBOT = 95, 960, 755, 825
SPREAD_MAX = 0.09    # 0.077 (EXODUS' two NOUNs) reads as fine to the eye; the defect was 0.197
# Per-type bands, measured over the 28 undisputed faces and widened by ~25%. A single
# global band does not work: NOUN is a solid book and legitimately runs twice as dark as
# an outline frame, while the bracket-only slots (PAIR, ANY, SAME_TYPE) are near-empty.
ICON_BANDS = {
    "NOUN":      (0.105, 0.290),
    "VERB":      (0.070, 0.175),
    "ADJECTIVE": (0.095, 0.195),
    "NAME":      (0.090, 0.210),
    "TITLE":     (0.070, 0.190),
}


def icon_fills(path: Path, composition: list[str]) -> list[float]:
    im = Image.open(path).convert("L")
    if im.size != (1024, 1536):
        im = im.resize((1024, 1536), Image.Resampling.LANCZOS)
    px = im.load(); n = len(composition); span = (X1 - X0) / n; out = []
    for i in range(n):
        a, b = int(X0 + i * span) + 10, int(X0 + (i + 1) * span) - 10
        dark = sum(1 for y in range(ITOP, IBOT) for x in range(a, b) if px[x, y] < 110)
        out.append(dark / max((b - a) * (IBOT - ITOP), 1))
    return out


def check_icons(path: Path, composition: list[str]) -> list[str]:
    """Repeated types must match, and every glyph must sit in the set's band."""
    f = icon_fills(path, composition); issues = []
    by: dict[str, list[float]] = {}
    for t, v in zip(composition, f):
        by.setdefault(t, []).append(v)
    for t, vs in by.items():
        if len(vs) > 1 and max(vs) - min(vs) > SPREAD_MAX:
            issues.append(f"{t} icons differ within the card: {[round(v,3) for v in vs]}")
        band = ICON_BANDS.get(t)             # bracket-only slots have no glyph to judge
        if not band:
            continue
        lo, hi = band
        for v in vs:
            if v > hi:
                issues.append(f"{t} glyph is too filled for the set ({v:.3f} > {hi})")
            elif v < lo:
                issues.append(f"{t} glyph is too light for the set ({v:.3f} < {lo})")
    return issues


def check_content(path: Path, rule: dict, flavor: str, model: str | None = None) -> list[str]:
    """Transcribe the printed fields and compare them to the rules record."""
    prompt = (
        "This is a finished Lot card. Transcribe EXACTLY what is printed, with no correction "
        "or interpretation. Return ONLY JSON: "
        '{"name": "<big title>", "card_count": "<top-right count label>", '
        '"chapter_value": "<the CHAPTER VALUE line>", "portion_value": "<the PORTION VALUE line>", '
        '"composition": ["<each label in the slot row left to right, INCLUDING any bracket '
        'label such as PAIR or SAME TYPE printed above or below the slots it spans, in position>"], '
        '"verse": "<the italic verse line under the value banner, or empty>", '
        '"garbled": ["<any word that is misspelled or nonsense>"], '
        '"placeholders": ["<any placeholder such as Example verse text, Book 1:1, lorem, TBD>"]}'
    )
    try:
        d = _parse_json_response(_call_gemini(prompt, image_path=path, model=model))
    except Exception as e:
        return [f"content check unreadable: {e}"]
    issues = []
    if str(d.get("name", "")).strip().upper() != rule["name"].upper():
        issues.append(f"name printed {d.get('name')!r}, expected {rule['name']!r}")
    if str(rule["chapter_value"]) not in str(d.get("chapter_value", "")):
        issues.append(f"chapter value printed {d.get('chapter_value')!r}, expected {rule['chapter_value']} points")
    pv = str(d.get("portion_value", "")).upper()
    if "PORTION" not in pv or f"{rule['visitor_letters']}/{rule['owner_letters']}" not in pv:
        issues.append(f"portion value printed {d.get('portion_value')!r}, expected PORTION VALUE: {rule['visitor_letters']}/{rule['owner_letters']} LETTERS")
    got = [str(x).strip().upper() for x in (d.get("composition") or [])]
    # A PAIR (and the other span constraints) prints ONE bracket label under the slots
    # it spans, not one label per slot, so collapse runs before comparing.
    want: list[str] = []
    for t in (x.upper() for x in rule["composition"]):
        if t in {"PAIR", "SAME_TYPE", "ONE_TYPE", "ANOTHER_TYPE", "ANY"} and want and want[-1] == t:
            continue
        want.append(t)
    if got != want:
        issues.append(f"composition printed {got}, expected {want}")
    if d.get("garbled"):
        issues.append(f"garbled text: {d['garbled']}")
    if d.get("placeholders"):
        issues.append(f"placeholder text: {d['placeholders']}")
    return issues
