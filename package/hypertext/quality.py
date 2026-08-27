"""Deterministic quality contracts and provenance for the card pipeline."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

QUALITY_GATE = 100
STAGES = ("plan", "prompt", "references", "image_request", "candidate",
          "composite", "revision", "review")
DIMENSIONS = ("composition", "typography", "template_fidelity", "metadata",
              "stat_pips", "artifact_cleanliness")


class QualityContractError(RuntimeError):
    pass


def _digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class StageProvenance:
    stage: str
    input_sha256: str
    output_sha256: str
    contract: str = "hypertext-quality/v1"
    status: str = "success"
    attempt: int = 1
    repaired: bool = False
    timestamp: str = ""

    def __post_init__(self) -> None:
        if self.stage not in STAGES:
            raise QualityContractError(f"unknown quality stage: {self.stage}")
        if self.status not in {"success", "failure"}:
            raise QualityContractError("stage status must be success or failure")
        if not 1 <= self.attempt <= 4:
            raise QualityContractError("stage attempts must be bounded to 1..4")


def provenance(stage: str, inputs: Any, outputs: Any, **kwargs: Any) -> StageProvenance:
    return StageProvenance(
        stage, _digest(inputs), _digest(outputs),
        timestamp=datetime.now(timezone.utc).isoformat(), **kwargs,
    )


def write_provenance(card_dir: Path, records: Iterable[StageProvenance]) -> Path:
    path = card_dir / "outputs" / "quality-provenance.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    prior = {}
    if path.exists():
        try:
            prior = {item["stage"]: item for item in json.loads(path.read_text())["stages"]}
        except (KeyError, ValueError, TypeError):
            prior = {}
    prior.update({r.stage: asdict(r) for r in records})
    payload = {"contract": "hypertext-quality/v1", "stages": list(prior.values())}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def validate_plan(card: dict) -> None:
    content = card.get("content", {})
    required = ("NUMBER", "WORD", "CARD_TYPE", "RARITY_TEXT", "ART_PROMPT",
                "STAT_LORE", "STAT_CONTEXT", "STAT_COMPLEXITY")
    missing = [key for key in required if content.get(key) in (None, "")]
    if missing:
        raise QualityContractError(f"plan missing required fields: {', '.join(missing)}")
    for key in ("STAT_LORE", "STAT_CONTEXT", "STAT_COMPLEXITY"):
        if not isinstance(content[key], int) or not 0 <= content[key] <= 5:
            raise QualityContractError(f"{key} must be an integer from 0 to 5")


def assemble_art_prompt(card: dict) -> str:
    """Prompt Gemini for art only; deterministic compositing owns all typography."""
    validate_plan(card)
    art = card["content"]["ART_PROMPT"].strip()
    return (f"Create only the illustration for this card's art panel: {art}\n"
            "No words, letters, numerals, captions, logos, watermarks, borders, UI, "
            "stat pips, badges, or card frame. Leave typography and metadata to the renderer.")


def select_references(refs: Iterable[dict], *, card_type: str, rarity: str,
                      limit: int = 4) -> list[dict]:
    """Stable, fidelity-first reference selection with explicit reasons."""
    ranked = sorted(refs, key=lambda r: (
        -(r.get("card_type") == card_type), -(r.get("rarity") == rarity),
        -int(r.get("quality_score", 0)), str(r.get("path", ""))))
    selected = []
    for ref in ranked:
        if int(ref.get("quality_score", 0)) != QUALITY_GATE:
            continue
        item = dict(ref)
        item["selection_reason"] = "type+rarity+100-score"
        selected.append(item)
        if len(selected) == limit:
            break
    return selected


def select_candidate(candidates: Iterable[dict]) -> dict:
    """Select the best valid decoded candidate; never accept timeout/no-output."""
    valid = [c for c in candidates if c.get("status") == "success" and c.get("image_bytes")]
    if not valid:
        raise QualityContractError("no successful image candidate")
    return max(valid, key=lambda c: (int(c.get("contract_score", 0)),
                                     -int(c.get("index", 0))))


def quality_score(scores: dict[str, int]) -> dict:
    unknown = set(scores) - set(DIMENSIONS)
    missing = set(DIMENSIONS) - set(scores)
    if unknown or missing:
        raise QualityContractError(f"invalid score dimensions; missing={sorted(missing)}, unknown={sorted(unknown)}")
    if any(not isinstance(v, int) or not 0 <= v <= 100 for v in scores.values()):
        raise QualityContractError("quality scores must be integers from 0 to 100")
    total = min(scores.values())  # weakest boundary wins; averages cannot hide defects
    return {"dimensions": dict(scores), "score": total, "passed": total == QUALITY_GATE,
            "gate": QUALITY_GATE}


def deterministic_repairs(issues: Iterable[str]) -> list[str]:
    allowed = {"dimensions": "normalize_dimensions", "format": "convert_to_png",
               "stat_pips": "redraw_stat_pips", "metadata": "rerender_metadata"}
    repairs = []
    for issue in issues:
        if issue not in allowed:
            raise QualityContractError(f"non-deterministic repair forbidden: {issue}")
        repairs.append(allowed[issue])
    return repairs
