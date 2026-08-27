"""Validated reference packs for full-card Gemini generation.

The pack is the boundary between reference discovery and Gemini.  Positions,
roles, rarity labels, digests, and role labels are serialized together so the
consumer cannot reinterpret a correctly selected path at the wrong position.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
FINISHED_REFERENCE_MANIFEST = (
    ROOT / "templates" / "card" / "v001" / "finished-card-references.json"
)
CONTRACT = "hypertext.gemini.reference-pack/v1"
FINISHED_REFERENCE_CONTRACT = "hypertext.finished-card-references/v1"
MAX_EXAMPLE_REFERENCES = 3
MAX_GEMINI_REFERENCES = 16
WORD_TYPES = {"NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE"}
RARITIES = {"COMMON", "UNCOMMON", "RARE", "GLORIOUS"}
FORBIDDEN_ASSET_MARKERS = ("legacy", "rejected", "superseded", "noncanonical")


class ReferenceContractError(ValueError):
    """A reference pack or candidate violates the full-card input contract."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_recipe_sha256(recipe: dict[str, Any]) -> str:
    payload = json.dumps(
        recipe, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )
    return sha256_text(payload)


def _stored_path(path: Path, root: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _resolved_path(path: str, root: Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def _gemini_label(position: int, role: str, card_type: str, rarity: str) -> str:
    if role == "current_card":
        return (
            f"[{position}] = CURRENT_CARD: card being fixed; preserve it except for "
            "the requested corrections"
        )
    if role == "template":
        return (
            f"[{position}] = TEMPLATE: SHA-256-verified {card_type} {rarity} "
            "structural layout/frame reference"
        )
    if role == "example":
        return (
            f"[{position}] = EXAMPLE: eligible finished {card_type} {rarity} "
            "card selected by deterministic similarity"
        )
    raise ReferenceContractError(f"unknown reference role: {role}")


@dataclass(frozen=True)
class ReferenceEntry:
    position: int
    role: str
    path: str
    sha256: str
    card_type: str
    rarity: str
    rarity_label: str
    gemini_label: str
    eligible: bool
    eligibility_reasons: tuple[str, ...]
    similarity_score: int | None
    similarity_reason: str
    similarity_components: dict[str, int]
    source_manifest: str | None = None
    source_manifest_sha256: str | None = None
    template_version: str | None = None
    template_commit: str | None = None
    template_manifest_status: str | None = None
    template_manifest_schema_version: int | None = None
    recipe_path: str | None = None
    recipe_sha256: str | None = None
    prompt_path: str | None = None
    prompt_sha256: str | None = None
    metadata_path: str | None = None
    metadata_sha256: str | None = None
    review_evidence_path: str | None = None
    review_evidence_sha256: str | None = None

    def resolved_path(self, root: Path) -> Path:
        return _resolved_path(self.path, root)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["eligibility_reasons"] = list(self.eligibility_reasons)
        value["assigned_role"] = self.role
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ReferenceEntry":
        data = dict(value)
        assigned_role = data.pop("assigned_role", data.get("role"))
        if assigned_role != data.get("role"):
            raise ReferenceContractError("serialized assigned role disagrees with role")
        data["eligibility_reasons"] = tuple(data.get("eligibility_reasons", ()))
        return cls(**data)


@dataclass(frozen=True)
class ReferencePack:
    mode: str
    target_type: str
    target_rarity: str
    repo_root: str
    max_examples: int
    references: tuple[ReferenceEntry, ...]
    candidate_audit: tuple[dict[str, Any], ...] = ()
    contract: str = CONTRACT
    selection_contract: str = (
        "exact type+rarity eligibility; accepted, finished, nonlegacy, nonsuperseded, "
        "SHA-256-verified assets only; rank by 35% art tokens + 30% semantic content "
        "+ 20% serialized prompt tokens + 15% stat proximity; break ties by SHA-256 then path"
    )

    @property
    def root(self) -> Path:
        return Path(self.repo_root)

    @property
    def paths(self) -> list[str]:
        return [str(item.resolved_path(self.root)) for item in self.references]

    @property
    def rarity_labels(self) -> dict[int, str]:
        return {item.position: item.rarity_label for item in self.references}

    @property
    def fix_mode(self) -> bool:
        return self.mode == "fix"

    @property
    def template(self) -> ReferenceEntry:
        return next(item for item in self.references if item.role == "template")

    @property
    def examples(self) -> tuple[ReferenceEntry, ...]:
        return tuple(item for item in self.references if item.role == "example")

    def __iter__(self):
        """Preserve the old private tuple API while keeping one source of truth."""
        yield self.paths
        yield self.rarity_labels
        yield self.fix_mode

    def validate(self, *, verify_files: bool = True) -> "ReferencePack":
        if self.contract != CONTRACT:
            raise ReferenceContractError(f"unsupported reference pack contract: {self.contract}")
        if self.mode not in {"generate", "fix"}:
            raise ReferenceContractError("reference pack mode must be generate or fix")
        if self.target_type not in WORD_TYPES or self.target_rarity not in RARITIES:
            raise ReferenceContractError("reference pack target type/rarity is invalid")
        if not 0 <= self.max_examples <= MAX_GEMINI_REFERENCES - 2:
            raise ReferenceContractError("reference pack example bound is invalid")
        if not self.references or len(self.references) > MAX_GEMINI_REFERENCES:
            raise ReferenceContractError("reference pack must contain 1..16 references")
        if [item.position for item in self.references] != list(range(1, len(self.references) + 1)):
            raise ReferenceContractError("reference positions must be consecutive and 1-indexed")
        expected_roles = (["current_card", "template"] if self.fix_mode else ["template"])
        expected_roles += ["example"] * (len(self.references) - len(expected_roles))
        if [item.role for item in self.references] != expected_roles:
            raise ReferenceContractError(
                "reference roles violate generate/fix position contract: " + ",".join(expected_roles)
            )
        if len(self.examples) > self.max_examples:
            raise ReferenceContractError("reference pack exceeds its top-X example bound")
        seen: set[Path] = set()
        for item in self.references:
            if not item.eligible:
                raise ReferenceContractError(f"selected reference is not eligible: {item.path}")
            if (item.card_type, item.rarity, item.rarity_label) != (
                self.target_type, self.target_rarity, self.target_rarity
            ):
                raise ReferenceContractError(f"reference type/rarity label mismatch: {item.path}")
            if item.gemini_label != _gemini_label(
                item.position, item.role, self.target_type, self.target_rarity
            ):
                raise ReferenceContractError(f"Gemini role label drift at position {item.position}")
            if not re.fullmatch(r"[0-9a-f]{64}", item.sha256):
                raise ReferenceContractError(f"reference lacks a valid SHA-256: {item.path}")
            path = item.resolved_path(self.root).resolve()
            if path in seen:
                raise ReferenceContractError(f"duplicate reference path: {item.path}")
            seen.add(path)
            if verify_files:
                if not path.is_file():
                    raise ReferenceContractError(f"reference file is missing: {item.path}")
                if sha256_file(path) != item.sha256:
                    raise ReferenceContractError(f"reference failed SHA-256 verification: {item.path}")
                if item.source_manifest:
                    manifest_path = _resolved_path(item.source_manifest, self.root)
                    if (not manifest_path.is_file() or not item.source_manifest_sha256
                            or sha256_file(manifest_path) != item.source_manifest_sha256):
                        raise ReferenceContractError(
                            f"reference source manifest failed SHA-256 verification: {item.path}"
                        )
                if item.role == "example":
                    evidence = (
                        (item.recipe_path, item.recipe_sha256, "recipe"),
                        (item.prompt_path, item.prompt_sha256, "prompt"),
                        (item.metadata_path, item.metadata_sha256, "metadata"),
                        (item.review_evidence_path, item.review_evidence_sha256, "review evidence"),
                    )
                    for evidence_path, evidence_sha, label in evidence:
                        resolved = _resolved_path(evidence_path or "", self.root)
                        if (not evidence_path or not evidence_sha or not resolved.is_file()
                                or sha256_file(resolved) != evidence_sha):
                            raise ReferenceContractError(
                                f"example {label} failed SHA-256 verification: {item.path}"
                            )
        template = self.template
        if not template.template_version or not template.source_manifest:
            raise ReferenceContractError("template reference lacks manifest/version provenance")
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "mode": self.mode,
            "target_type": self.target_type,
            "target_rarity": self.target_rarity,
            "repo_root": self.repo_root,
            "max_examples": self.max_examples,
            "selection_contract": self.selection_contract,
            "references": [item.to_dict() for item in self.references],
            "candidate_audit": list(self.candidate_audit),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any], *, verify_files: bool = True) -> "ReferencePack":
        pack = cls(
            contract=value.get("contract", ""),
            mode=value.get("mode", ""),
            target_type=value.get("target_type", ""),
            target_rarity=value.get("target_rarity", ""),
            repo_root=value.get("repo_root", ""),
            max_examples=int(value.get("max_examples", 0)),
            selection_contract=value.get("selection_contract", ""),
            references=tuple(ReferenceEntry.from_dict(item) for item in value.get("references", ())),
            candidate_audit=tuple(value.get("candidate_audit", ())),
        )
        return pack.validate(verify_files=verify_files)

    def write(self, path: Path) -> Path:
        self.validate()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    @classmethod
    def read(cls, path: Path, *, verify_files: bool = True) -> "ReferencePack":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")), verify_files=verify_files)


def _tokens(value: Any) -> set[str]:
    if isinstance(value, (list, tuple)):
        value = " ".join(str(item) for item in value)
    return set(re.findall(r"[a-z0-9]+", str(value).lower()))


def _jaccard_bp(left: Any, right: Any) -> int:
    left_tokens, right_tokens = _tokens(left), _tokens(right)
    union = left_tokens | right_tokens
    return 0 if not union else len(left_tokens & right_tokens) * 10_000 // len(union)


def _recipe_content(recipe: dict[str, Any]) -> dict[str, Any]:
    content = recipe.get("content", recipe)
    return content if isinstance(content, dict) else {}


def _semantic_text(content: dict[str, Any]) -> str:
    fields = (
        "WORD", "GLOSS", "ABILITY_TEXT", "OT_VERSE_LINE", "NT_VERSE_LINE",
        "HEBREW_TRANSLIT", "GREEK_TRANSLIT", "TRIVIA_BULLETS",
    )
    return " ".join(str(content.get(field, "")) for field in fields)


def _similarity(
    target_recipe: dict[str, Any],
    target_prompt: str,
    candidate_recipe: dict[str, Any],
    candidate_prompt: str,
) -> tuple[int, dict[str, int], str]:
    target, candidate = _recipe_content(target_recipe), _recipe_content(candidate_recipe)
    art = _jaccard_bp(target.get("ART_PROMPT", ""), candidate.get("ART_PROMPT", ""))
    semantic = _jaccard_bp(_semantic_text(target), _semantic_text(candidate))
    prompt = _jaccard_bp(target_prompt, candidate_prompt)
    stat_fields = ("STAT_LORE", "STAT_CONTEXT", "STAT_COMPLEXITY")
    if all(isinstance(target.get(field), int) and isinstance(candidate.get(field), int)
           for field in stat_fields):
        distance = sum(abs(target[field] - candidate[field]) for field in stat_fields)
        stats = max(0, 15 - distance) * 10_000 // 15
    else:
        stats = 0
    components = {
        "art_prompt_token_jaccard_bp": art,
        "semantic_content_token_jaccard_bp": semantic,
        "serialized_prompt_token_jaccard_bp": prompt,
        "stat_proximity_bp": stats,
    }
    score = (35 * art + 30 * semantic + 20 * prompt + 15 * stats) // 100
    reason = (
        f"weighted_similarity={score}; art={art}*35%, semantic={semantic}*30%, "
        f"serialized_prompt={prompt}*20%, stats={stats}*15%; "
        "tie_break=sha256,path"
    )
    return score, components, reason


def _candidate_paths(entry: dict[str, Any], root: Path) -> tuple[Path, Path, Path]:
    return tuple(_resolved_path(str(entry.get(key, "")), root) for key in (
        "path", "recipe_path", "prompt_path"
    ))  # type: ignore[return-value]


def _evaluate_candidate(
    entry: dict[str, Any],
    *,
    root: Path,
    target_type: str,
    target_rarity: str,
    target_recipe: dict[str, Any],
    target_prompt: str,
    current_card_path: Path | None,
    manifest_path: Path,
    manifest_sha256: str,
) -> dict[str, Any]:
    image_path, recipe_path, prompt_path = _candidate_paths(entry, root)
    reasons: list[str] = []
    status = str(entry.get("status", "")).lower()
    if status != "accepted":
        reasons.append(f"status={status or 'missing'}")
    if entry.get("finished") is not True:
        reasons.append("finished!=true")
    if entry.get("legacy") is not False:
        reasons.append("legacy!=false")
    if entry.get("superseded_by"):
        reasons.append(f"superseded_by={entry['superseded_by']}")
    lowered_parts = [part.lower() for part in image_path.parts]
    if any(marker in part for marker in FORBIDDEN_ASSET_MARKERS for part in lowered_parts):
        reasons.append("forbidden_path_marker")
    manifest_type = str(entry.get("card_type", "")).upper()
    manifest_rarity = str(entry.get("rarity", "")).upper()
    if manifest_type != target_type:
        reasons.append(f"target_type_mismatch={manifest_type or 'missing'}")
    if manifest_rarity != target_rarity:
        reasons.append(f"target_rarity_mismatch={manifest_rarity or 'missing'}")
    if current_card_path and image_path.resolve() == current_card_path.resolve():
        reasons.append("current_card_excluded")

    expected_sha = str(entry.get("sha256", "")).lower()
    actual_sha = None
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        reasons.append("missing_or_invalid_expected_sha256")
    elif not image_path.is_file():
        reasons.append("image_missing")
    else:
        try:
            actual_sha = sha256_file(image_path)
            if actual_sha != expected_sha:
                reasons.append("image_sha256_mismatch")
        except OSError:
            reasons.append("image_unreadable")

    candidate_recipe: dict[str, Any] = {}
    recipe_sha = None
    if not recipe_path.is_file():
        reasons.append("recipe_missing")
    else:
        try:
            loaded_recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
            if not isinstance(loaded_recipe, dict):
                raise TypeError("recipe must be an object")
            candidate_recipe = loaded_recipe
            recipe_sha = sha256_file(recipe_path)
        except (OSError, ValueError, TypeError):
            reasons.append("recipe_invalid")
        content = _recipe_content(candidate_recipe)
        recipe_type = str(content.get("CARD_TYPE") or content.get("TYPE") or "").upper()
        recipe_rarity = str(content.get("RARITY_TEXT") or "").upper()
        if recipe_type != manifest_type:
            reasons.append(f"recipe_type_mismatch={recipe_type or 'missing'}")
        if recipe_rarity != manifest_rarity:
            reasons.append(f"recipe_rarity_mismatch={recipe_rarity or 'missing'}")

    candidate_prompt = ""
    prompt_sha = None
    if not prompt_path.is_file():
        reasons.append("prompt_missing")
    else:
        try:
            candidate_prompt = prompt_path.read_text(encoding="utf-8")
            prompt_sha = sha256_file(prompt_path)
        except (OSError, UnicodeError):
            reasons.append("prompt_invalid")

    metadata_path_value = entry.get("metadata_path")
    metadata_path = _resolved_path(str(metadata_path_value or ""), root)
    metadata_sha = None
    if not metadata_path_value or not metadata_path.is_file():
        reasons.append("metadata_missing")
    else:
        try:
            metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
            if not isinstance(metadata, dict):
                raise TypeError("metadata must be an object")
            metadata_sha = sha256_file(metadata_path)
            metadata_type = str(metadata.get("card_type") or metadata.get("type") or "").upper()
            metadata_rarity = str(metadata.get("rarity") or "").upper()
            if metadata_type != manifest_type:
                reasons.append(f"metadata_type_mismatch={metadata_type or 'missing'}")
            if metadata_rarity != manifest_rarity:
                reasons.append(f"metadata_rarity_mismatch={metadata_rarity or 'missing'}")
        except (OSError, ValueError, TypeError):
            reasons.append("metadata_invalid")

    review = entry.get("review", {})
    if not isinstance(review, dict) or str(review.get("status", "")).lower() not in {
        "accepted", "green"
    } or review.get("score") != 100:
        reasons.append("review_not_accepted_at_100")
    evidence_path_value = review.get("evidence_path") if isinstance(review, dict) else None
    evidence_path = _resolved_path(str(evidence_path_value or ""), root)
    evidence_sha = None
    if not evidence_path_value:
        reasons.append("review_evidence_missing")
    else:
        if not evidence_path.is_file():
            reasons.append("review_evidence_missing")
        else:
            try:
                evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
                if not isinstance(evidence, dict):
                    raise TypeError("review evidence must be an object")
                evidence_sha = sha256_file(evidence_path)
                if (evidence.get("passed") is not True or evidence.get("score") != 100
                        or str(evidence.get("card_type", "")).upper() != manifest_type
                        or str(evidence.get("rarity", "")).upper() != manifest_rarity):
                    reasons.append("review_evidence_mismatch")
            except (OSError, ValueError, TypeError):
                reasons.append("review_evidence_invalid")

    eligible = not reasons
    if eligible:
        eligibility_reasons = [
            "status=accepted", "finished=true", "legacy=false", "not_superseded",
            "sha256=verified", "type=exact_match", "rarity=exact_match",
            "recipe_and_prompt=present", "review=accepted_100",
        ]
        similarity_score, similarity_components, similarity_reason = _similarity(
            target_recipe, target_prompt, candidate_recipe, candidate_prompt
        )
    else:
        eligibility_reasons = reasons
        similarity_score, similarity_components = None, {}
        similarity_reason = "not_scored_ineligible"

    return {
        "id": entry.get("id"),
        "path": _stored_path(image_path, root),
        "sha256": expected_sha or None,
        "actual_sha256": actual_sha,
        "card_type": manifest_type,
        "rarity": manifest_rarity,
        "eligible": eligible,
        "eligibility_reasons": eligibility_reasons,
        "similarity_score": similarity_score,
        "similarity_components": similarity_components,
        "similarity_reason": similarity_reason,
        "recipe_path": _stored_path(recipe_path, root),
        "recipe_sha256": recipe_sha,
        "prompt_path": _stored_path(prompt_path, root),
        "prompt_sha256": prompt_sha,
        "metadata_path": _stored_path(metadata_path, root),
        "metadata_sha256": metadata_sha,
        "review_evidence_path": (
            _stored_path(evidence_path, root) if evidence_path_value else None
        ),
        "review_evidence_sha256": evidence_sha,
        "source_manifest": _stored_path(manifest_path, root),
        "source_manifest_sha256": manifest_sha256,
        "selected": False,
    }


def build_reference_pack(
    *,
    template_record: dict[str, Any],
    target_type: str,
    target_rarity: str,
    target_recipe: dict[str, Any] | None = None,
    target_prompt: str = "",
    current_card_path: Path | None = None,
    fix_mode: bool = False,
    max_examples: int = MAX_EXAMPLE_REFERENCES,
    manifest_path: Path = FINISHED_REFERENCE_MANIFEST,
    root: Path = ROOT,
) -> ReferencePack:
    """Build a strict pack from the canonical template and curated finished cards."""
    target_type, target_rarity = target_type.upper(), target_rarity.upper()
    if target_type not in WORD_TYPES or target_rarity not in RARITIES:
        raise ReferenceContractError("target type/rarity is invalid")
    if not 0 <= max_examples <= MAX_GEMINI_REFERENCES - 2:
        raise ReferenceContractError("max_examples must be between 0 and 14")
    if fix_mode and (current_card_path is None or not current_card_path.is_file()):
        raise ReferenceContractError("fix mode requires an existing current card at position [1]")
    if not manifest_path.is_file():
        raise ReferenceContractError(f"finished-card reference manifest is missing: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        raise ReferenceContractError("finished-card reference manifest is invalid JSON") from exc
    if not isinstance(manifest, dict):
        raise ReferenceContractError("finished-card reference manifest must be an object")
    if manifest.get("contract") != FINISHED_REFERENCE_CONTRACT:
        raise ReferenceContractError("finished-card reference manifest contract is invalid")
    if manifest.get("status") != "curated":
        raise ReferenceContractError("finished-card reference manifest is not curated")
    manifest_entries = manifest.get("entries")
    if not isinstance(manifest_entries, list):
        raise ReferenceContractError("finished-card reference manifest entries must be a list")
    if not all(isinstance(entry, dict) for entry in manifest_entries):
        raise ReferenceContractError("finished-card reference manifest entries must be objects")
    manifest_sha = sha256_file(manifest_path)
    target_recipe = target_recipe or {}
    if not isinstance(target_recipe, dict):
        raise ReferenceContractError("target recipe must be an object")
    if not isinstance(target_prompt, str):
        raise ReferenceContractError("target prompt must be a string")
    audits = [
        _evaluate_candidate(
            entry,
            root=root,
            target_type=target_type,
            target_rarity=target_rarity,
            target_recipe=target_recipe,
            target_prompt=target_prompt,
            current_card_path=current_card_path,
            manifest_path=manifest_path,
            manifest_sha256=manifest_sha,
        )
        for entry in manifest_entries
    ]
    eligible = sorted(
        (item for item in audits if item["eligible"]),
        key=lambda item: (-int(item["similarity_score"]), item["sha256"], item["path"]),
    )
    selected_paths = {item["path"] for item in eligible[:max_examples]}
    audits = [{**item, "selected": item["path"] in selected_paths} for item in audits]

    references: list[ReferenceEntry] = []
    if fix_mode and current_card_path:
        position = 1
        current_sha256 = sha256_file(current_card_path)
        # The generator normally overwrites the current output path. Preserve the
        # exact bytes Gemini saw at a content-addressed input path so later
        # provenance validation cannot accidentally hash the replacement output.
        snapshot = (
            current_card_path.parent / "reference-inputs" /
            f"current-{current_sha256}.png"
        )
        if not snapshot.is_file() or sha256_file(snapshot) != current_sha256:
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_bytes(current_card_path.read_bytes())
        references.append(ReferenceEntry(
            position=position,
            role="current_card",
            path=_stored_path(snapshot, root),
            sha256=current_sha256,
            card_type=target_type,
            rarity=target_rarity,
            rarity_label=target_rarity,
            gemini_label=_gemini_label(position, "current_card", target_type, target_rarity),
            eligible=True,
            eligibility_reasons=("existing_current_card", "sha256=verified", "requested_fix_source"),
            similarity_score=0,
            similarity_reason="not_applicable_current_card",
            similarity_components={},
        ))

    template_position = 2 if fix_mode else 1
    template_path = Path(template_record["path"])
    if (str(template_record.get("type", "")).upper(),
            str(template_record.get("rarity", "")).upper()) != (target_type, target_rarity):
        raise ReferenceContractError("resolved template record does not match target type/rarity")
    references.append(ReferenceEntry(
        position=template_position,
        role="template",
        path=_stored_path(template_path, root),
        sha256=str(template_record["sha256"]),
        card_type=target_type,
        rarity=target_rarity,
        rarity_label=target_rarity,
        gemini_label=_gemini_label(template_position, "template", target_type, target_rarity),
        eligible=True,
        eligibility_reasons=(
            "operator_accepted_canonical_manifest", "exact_type_rarity_cell", "sha256=verified",
        ),
        similarity_score=0,
        similarity_reason="authoritative_structure_not_ranked",
        similarity_components={},
        source_manifest=_stored_path(Path(template_record["manifest_path"]), root),
        source_manifest_sha256=template_record.get("manifest_sha256"),
        template_version=template_record.get("template_version"),
        template_commit=template_record.get("template_commit"),
        template_manifest_status=template_record.get("manifest_status"),
        template_manifest_schema_version=template_record.get("manifest_schema_version"),
    ))

    for audit in eligible[:max_examples]:
        position = len(references) + 1
        references.append(ReferenceEntry(
            position=position,
            role="example",
            path=audit["path"],
            sha256=audit["sha256"],
            card_type=target_type,
            rarity=target_rarity,
            rarity_label=target_rarity,
            gemini_label=_gemini_label(position, "example", target_type, target_rarity),
            eligible=True,
            eligibility_reasons=tuple(audit["eligibility_reasons"]),
            similarity_score=audit["similarity_score"],
            similarity_reason=audit["similarity_reason"],
            similarity_components=audit["similarity_components"],
            source_manifest=audit["source_manifest"],
            source_manifest_sha256=audit["source_manifest_sha256"],
            recipe_path=audit["recipe_path"],
            recipe_sha256=audit["recipe_sha256"],
            prompt_path=audit["prompt_path"],
            prompt_sha256=audit["prompt_sha256"],
            metadata_path=audit["metadata_path"],
            metadata_sha256=audit["metadata_sha256"],
            review_evidence_path=audit["review_evidence_path"],
            review_evidence_sha256=audit["review_evidence_sha256"],
        ))

    pack = ReferencePack(
        mode="fix" if fix_mode else "generate",
        target_type=target_type,
        target_rarity=target_rarity,
        repo_root=str(root.resolve()),
        max_examples=max_examples,
        references=tuple(references),
        candidate_audit=tuple(audits),
    )
    return pack.validate()
