"""Art subjects, motif caps and the lighting palette.

User (2026-08-29): "we have way too many towers in our arts." At 76 cards,
14 art prompts showed the tower or ziggurat and only about five of those were
tower words; 45 of 76 carried the same lighting clause ("one radiant golden
light source") because every batch module appended one fixed STYLE string.

Three rules, all read from series/<series>/set-standards.yml (`art:`):

- SUBJECT: the illustration depicts the card's own OT-verse scene. The tower
  appears only for words on `tower_allowlist`; the plan phase fails closed on
  any other prompt that names it.
- MOTIF CAPS: `motif_caps` bounds how many prompts in the set may share one
  motif (tower, city, plain, tent, water); `hypertext art-audit` reports the
  histogram, and scripts/pipeline/offline_check.py prints a batch beside it.
- LIGHTING: every prompt ends with one clause from `lighting_palette`. The
  fixed `medium` clause carries the painterly style; the lighting clause
  carries the mood. GOLDEN IS THE DEFAULT and is not rationed: it is the
  set's established signature, restored at the user's own request from the
  printed cards. Another clause is for a scene that genuinely needs it - a
  night, a storm, firelight, underwater. The spread is reported, never
  enforced (user, 2026-08-29: "I don't know why lighting is super important
  here" - the complaint was towers, a subject problem, not the light).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

MOTIFS: dict[str, str] = {
    "tower": r"\btowers?\b|\bziggurats?\b",
    "city": r"\bcity\b|\bcities\b|\bcity walls?\b|\bramparts?\b",
    "plain": r"\bplains?\b",
    "tent": r"\btents?\b",
    "water": r"\briver\b|\bflood\b|\bfloodwaters?\b|\bwaters?\b|\bsea\b|\brain\b",
    "garden": r"\bgarden\b|\borchard\b",
    "altar": r"\baltar\b",
    "field": r"\bfields?\b|\bfurrows?\b|\bvineyard\b",
    "mountain": r"\bmountains?\b|\bhills?\b|\bridge\b",
    "sky": r"\bstars?\b|\bmoon\b|\bsun\b",
}

# Fallback keys so legacy prompts written before the palette are still
# assigned a lighting clause by their wording.
LIGHTING_KEYS: dict[str, str] = {
    "golden": r"radiant golden|golden light",
    "dawn": r"\bdawn\b|sunrise",
    "noon": r"\bnoon\b|glare",
    "storm": r"\bstorm\b|thunder",
    "lantern": r"\blantern\b|\bcandle",
    "firelight": r"firelight|\bflames?\b|\bfire\b|\bkiln\b|\bfurnace\b",
    "underwater": r"underwater|\bbeneath the (?:water|sea)",
    "overcast": r"overcast|\bgrey\b|\bmist\b|\bfog\b",
    "desert": r"\bdesert\b|\bwilderness\b|\brust\b",
    "moonlit": r"moonlit|\bmoonlight\b|silver-blue",
}

DEFAULT_ART = {
    "tower_allowlist": ["BUILD", "BRICK", "CITY", "SHINAR", "HIGH", "ASCEND", "SCATTER", "CONFUSE"],
    "motif_caps": {"tower": 8, "city": 10, "plain": 10, "tent": 8, "water": 12},
    "lighting_share_cap": None,   # reporting only; golden is the set's signature
    "medium": "luminous cinematic oil painting with impressionistic brushwork, saturated full colour, a strong symbolic subject, no engraving or line art",
    "lighting_palette": [
        {"name": "golden", "clause": "deep shadowed background lit by one radiant golden light source, rich saturated blues and golds"},
        {"name": "dawn", "clause": "cold blue dawn light with long violet shadows and a pale rose horizon"},
        {"name": "noon", "clause": "hard white noon glare, bleached ochre ground and short black shadows"},
        {"name": "storm", "clause": "storm light under a bruised green-grey sky, one shaft of silver breaking through"},
        {"name": "lantern", "clause": "night under a lantern, a warm amber pool of light in deep indigo dark"},
        {"name": "firelight", "clause": "firelight from below, red and orange on stone, smoke against black"},
        {"name": "underwater", "clause": "underwater green-gold light filtering down through murky depth"},
        {"name": "overcast", "clause": "overcast grey-blue daylight, soft and shadowless, wet colours saturated"},
        {"name": "desert", "clause": "red desert light of late afternoon, rust and copper against a turquoise sky"},
        {"name": "moonlit", "clause": "moonlit silver-blue with water and stone picked out in cool highlights"},
    ],
}


def load_art_standards(series_dir: str | Path) -> dict[str, Any]:
    path = Path(series_dir) / "set-standards.yml"
    art: dict[str, Any] = {}
    if yaml is not None and path.exists():
        try:
            art = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("art") or {}
        except (OSError, ValueError):
            art = {}
    merged = dict(DEFAULT_ART)
    merged.update({k: v for k, v in art.items() if v is not None})
    return merged


def motifs_in(prompt: str) -> set[str]:
    return {name for name, pattern in MOTIFS.items() if re.search(pattern, str(prompt), re.IGNORECASE)}


def lighting_of(prompt: str, art: dict[str, Any]) -> str | None:
    """The palette clause a prompt carries - by exact clause, else by its key words."""
    low = " ".join(str(prompt).split()).lower()
    for entry in art["lighting_palette"]:
        if str(entry["clause"]).lower() in low:
            return str(entry["name"])
    for name, pattern in LIGHTING_KEYS.items():
        if re.search(pattern, low):
            return name
    return None


def style_suffix(art: dict[str, Any], lighting: str) -> str:
    """The clause a designs module appends to an art prompt: medium + one palette entry."""
    for entry in art["lighting_palette"]:
        if entry["name"] == lighting:
            return f"{art['medium']}, {entry['clause']}"
    raise KeyError(f"unknown lighting {lighting!r}; palette: {[e['name'] for e in art['lighting_palette']]}")


def check_art_prompt(word: str, prompt: str, art: dict[str, Any]) -> list[str]:
    """Per-card hard rules: the tower only for tower words; a palette lighting clause present."""
    issues: list[str] = []
    w = str(word).strip().upper()
    if "tower" in motifs_in(prompt) and w not in {str(x).upper() for x in art["tower_allowlist"]}:
        issues.append(f"{w} is not a tower word: its art must depict the word's own verse scene, not the tower (allowlist: {', '.join(art['tower_allowlist'])})")
    # "a night sky crowded with stars" is not a crowd: the word has to be about people.
    crowd = (
        r"\bcrowds?\b|\bthrongs?\b|\bassembl(?:y|ies)\b"
        r"|\bcrowded with (?:people|figures|men|women|travellers|travelers)\b"
        r"|\b(?:gathering|multitude|group|line|procession)\s+of\s+(?:people|men|women|figures|travellers|travelers|worshippers|workers)\b"
    )
    if re.search(crowd, str(prompt), re.IGNORECASE):
        issues.append("art prompt describes a crowd; the figure rule needs no people or one figure seen from behind")
    if lighting_of(prompt, art) is None:
        issues.append("art prompt carries no lighting clause from the palette; end it with one of: " + ", ".join(e["name"] for e in art["lighting_palette"]))
    return issues


def load_series_prompts(series_dir: str | Path) -> list[tuple[str, str, str]]:
    rows = []
    for path in sorted(Path(series_dir).glob("cards/*/card.json")):
        try:
            c = json.loads(path.read_text(encoding="utf-8"))["content"]
            rows.append((path.parent.name, str(c["WORD"]), str(c["ART_PROMPT"])))
        except (OSError, ValueError, KeyError):
            continue
    return rows


def audit_series(series_dir: str | Path, extra: list[tuple[str, str, str]] | None = None) -> dict[str, Any]:
    """Motif and lighting histograms for the set (plus optional unplanned prompts) against the caps."""
    art = load_art_standards(series_dir)
    rows = load_series_prompts(series_dir) + list(extra or [])
    motif_hist: dict[str, list[str]] = {m: [] for m in MOTIFS}
    light_hist: dict[str, list[str]] = {}
    tower_offlist: list[str] = []
    allow = {str(x).upper() for x in art["tower_allowlist"]}
    for label, word, prompt in rows:
        ms = motifs_in(prompt)
        for m in ms:
            motif_hist[m].append(label)
        if "tower" in ms and word.upper() not in allow:
            tower_offlist.append(label)
        light_hist.setdefault(lighting_of(prompt, art) or "none", []).append(label)
    n = len(rows)
    over_motif = {m: len(v) for m, v in motif_hist.items() if m in art["motif_caps"] and len(v) > int(art["motif_caps"][m])}
    cap = art.get("lighting_share_cap")
    cap = float(cap) if cap is not None else None
    over_light: dict[str, int] = {}   # only populated when a series opts back in to a cap
    return {
        "cards": n,
        "motifs": motif_hist,
        "motif_caps": art["motif_caps"],
        "over_motif_caps": over_motif,
        "lighting": light_hist,
        "lighting_share_cap": cap,
        "over_lighting_cap": over_light,
        "tower_off_allowlist": tower_offlist,
        "allowlist": art["tower_allowlist"],
    }


__all__ = ["MOTIFS", "DEFAULT_ART", "load_art_standards", "motifs_in", "lighting_of", "style_suffix", "check_art_prompt", "audit_series", "load_series_prompts"]
