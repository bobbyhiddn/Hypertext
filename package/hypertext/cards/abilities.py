"""Semantic-first ability generation and rarity validation.

The card schema deliberately stores only the final ability copy.  This module
keeps the richer design trail separate so existing renderers and card records
remain compatible while the planner can prove how an ability was derived.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Callable


class AbilityGenerationError(RuntimeError):
    """Raised when no generated ability survives validation and criticism."""


DIMENSIONS = ("scope", "complexity", "setup", "interaction", "payoff")
CARD_TYPES = ("NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE")
RARITIES = ("COMMON", "UNCOMMON", "RARE", "GLORIOUS")
CRITIC_CATEGORIES = (
    "thematic_fidelity",
    "type_fidelity",
    "flavor_strength",
    "rarity_fit",
    "rules_legality",
    "operand_completeness",
    "rules_clarity",
)


# Ratings use one shared 0-3 scale.  Each rarity has an explicit range for
# every dimension plus a total range, which prevents a candidate from hiding
# an out-of-rarity effect behind a vague label such as "simple" or "unique".
RATING_SCALE = {
    "scope": {
        0: "no game object or player is affected",
        1: "one player, one zone, or a fixed group of at most three cards",
        2: "two players or zones, or one player's full hand or Pages",
        3: "all players, a global zone, or the chapter-wide game state",
    },
    "complexity": {
        0: "no resolution instruction",
        1: "one choice or one atomic resolution step",
        2: "two linked steps, or one condition with one result",
        3: "three linked steps, branching, or a repeated/scaling resolution",
    },
    "setup": {
        0: "works from the ordinary turn state without a prerequisite",
        1: "uses one ordinary zone, card type, or readily met condition",
        2: "needs a threshold, a specific Pages/Sheol state, or two prerequisites",
        3: "needs a demanding multi-part board or resource state",
    },
    "interaction": {
        0: "affects only the activating player and shared hidden information",
        1: "reveals, offers a choice to, or lightly benefits another player",
        2: "changes a target player's hand, resources, Pages, or choices",
        3: "changes every player or the turn/chapter structure",
    },
    "payoff": {
        0: "no material game effect",
        1: "minor filtering, ordering, information, or one-card-equivalent value",
        2: "clear card, Letter, protection, or tempo advantage",
        3: "multi-card swing, reset, scoring impact, or game-changing advantage",
    },
}


RARITY_BUDGETS = {
    "COMMON": {
        "dimensions": {
            "scope": {"min": 1, "max": 1},
            "complexity": {"min": 1, "max": 1},
            "setup": {"min": 0, "max": 0},
            "interaction": {"min": 0, "max": 0},
            "payoff": {"min": 1, "max": 1},
        },
        "total": {"min": 3, "max": 3},
        "intent": "immediate, self-contained, one-step value",
    },
    "UNCOMMON": {
        "dimensions": {
            "scope": {"min": 1, "max": 2},
            "complexity": {"min": 1, "max": 2},
            "setup": {"min": 0, "max": 1},
            "interaction": {"min": 0, "max": 1},
            "payoff": {"min": 1, "max": 2},
        },
        "total": {"min": 4, "max": 7},
        "intent": "one meaningful condition, type hook, choice, or light interaction",
    },
    "RARE": {
        "dimensions": {
            "scope": {"min": 1, "max": 2},
            "complexity": {"min": 2, "max": 3},
            "setup": {"min": 1, "max": 2},
            "interaction": {"min": 0, "max": 2},
            "payoff": {"min": 2, "max": 3},
        },
        "total": {"min": 7, "max": 11},
        "intent": "a substantial, earned effect with layered play or interaction",
    },
    "GLORIOUS": {
        "dimensions": {
            "scope": {"min": 2, "max": 3},
            "complexity": {"min": 2, "max": 3},
            "setup": {"min": 0, "max": 3},
            "interaction": {"min": 1, "max": 3},
            "payoff": {"min": 3, "max": 3},
        },
        "total": {"min": 10, "max": 15},
        "intent": "a broad, memorable effect that can materially redirect a chapter",
    },
}


TYPE_SEMANTIC_ROLES = {
    "NOUN": "Embody a person, place, thing, or concept as an object, state, resource, shelter, group, or relationship.",
    "VERB": "Embody an action or state-change as a visible change in game state.",
    "ADJECTIVE": "Embody a quality through comparison, qualification, strengthening, weakening, or a changed condition.",
    "NAME": "Embody a specific identity through its relationships, history, calling, place, or legacy.",
    "TITLE": "Embody a role or authority, including the TITLE rule that it may stand for NOUN or NAME when recorded.",
}


CANONICAL_RULE_TERMS = (
    "ability",
    "resolve",
    "Tower",
    "hand",
    "Pages",
    "Sheol",
    "Lot",
    "Lots",
    "Chapter",
    "Chapter Lot",
    "Letter",
    "Letters",
    "Wreath",
    "NOUN",
    "VERB",
    "ADJECTIVE",
    "NAME",
    "TITLE",
    "LORE",
    "CONTEXT",
    "COMPLEXITY",
    "card",
    "cards",
    "player",
    "players",
    "card type",
    "card types",
    "draw",
    "discard",
    "reveal",
    "look at",
    "put",
    "add",
    "return",
    "shuffle",
    "choose",
    "exchange",
    "gain",
    "spend",
    "record",
    "activate",
    "redeem",
    "name",
)

CANONICAL_ZONES = ("Tower", "hand", "Pages", "Sheol", "Lot", "Lots", "Chapter Lot")
CANONICAL_RULE_ACTIONS = (
    "draw",
    "discard",
    "reveal",
    "look at",
    "put",
    "add",
    "return",
    "shuffle",
    "choose",
    "exchange",
    "gain",
    "spend",
    "record",
    "activate",
    "redeem",
    "name",
)

_ACTION_PATTERNS = {
    "draw": re.compile(r"\bdraws?\b", re.IGNORECASE),
    "discard": re.compile(r"\bdiscards?\b", re.IGNORECASE),
    "reveal": re.compile(r"\breveals?\b", re.IGNORECASE),
    "look at": re.compile(r"\blooks?\s+at\b", re.IGNORECASE),
    "put": re.compile(r"\bputs?\b", re.IGNORECASE),
    "add": re.compile(r"\badds?\b", re.IGNORECASE),
    "return": re.compile(r"\breturns?\b", re.IGNORECASE),
    "shuffle": re.compile(r"\bshuffles?\b", re.IGNORECASE),
    "choose": re.compile(r"\bchooses?\b", re.IGNORECASE),
    "exchange": re.compile(r"\bexchanges?\b", re.IGNORECASE),
    "gain": re.compile(r"\bgains?\b", re.IGNORECASE),
    "spend": re.compile(r"\bspends?\b", re.IGNORECASE),
    "record": re.compile(r"\brecords?\b", re.IGNORECASE),
    "activate": re.compile(r"\bactivates?\b", re.IGNORECASE),
    "redeem": re.compile(r"\bredeems?\b", re.IGNORECASE),
    "name": re.compile(r"\bnames?\s+(?=(?:a|the|one|exactly|card)\b)", re.IGNORECASE),
}

_QUANTITY_PATTERN = re.compile(
    r"\b(?:exactly\s+|up\s+to\s+)?\d+\b|\b(?:a|an|one|all|each|every|any)\b|\bchosen\b",
    re.IGNORECASE,
)
_CARD_OR_RESOURCE_PATTERN = re.compile(
    r"\b(?:card|cards|hand|Lot|Lots|Letter|Letters|Wreath|Wreaths|player|players|card type|card types)\b",
    re.IGNORECASE,
)
_ZONE_PATTERN = re.compile(r"\b(?:Tower|hand|Pages|Sheol|Chapter Lot|Lots?|Lot)\b", re.IGNORECASE)
_AMBIGUOUS_REFERENCES = re.compile(
    r"\b(?:it|them|they|that many|this way|as normal|normally|the other)\b",
    re.IGNORECASE,
)
_CONDITION_PATTERN = re.compile(
    r"\b(?:if|unless|only if|for each|with at least|that (?:each )?share|matching)\b",
    re.IGNORECASE,
)
_ONGOING_PATTERN = re.compile(
    r"\b(?:until|during|for the rest of|next turn|this chapter|cannot|may not|counts as)\b",
    re.IGNORECASE,
)
_ACTOR_PREFIX = (
    r"(?:you(?:\s+and\s+(?:the\s+)?(?:chosen|other|target)\s+player)?|"
    r"(?:each|every|all)\s+players?|(?:the\s+)?(?:chosen|target|other|another)\s+player)"
)
_ACTOR_ACTION_PATTERN = re.compile(
    rf"\b{_ACTOR_PREFIX}\s+(?:each\s+)?(?:(?:may|must|can|cannot)\s+)?(?P<head>[a-z]+)\b",
    re.IGNORECASE,
)
_CONDITIONED_PLAYER_ACTION_PATTERN = re.compile(
    r"\b(?:each|every|all)\s+players?\s+with\b[^.;]{1,80}?"
    r"\b(?:hand|Pages|Sheol|Tower|Chapter Lot|Lots?|Letters?)\s+(?P<head>[a-z]+)\b",
    re.IGNORECASE,
)
_NON_ACTION_HEADS = {
    "are",
    "control",
    "controls",
    "has",
    "have",
    "is",
    "match",
    "matches",
    "share",
    "shares",
    "was",
    "were",
    "with",
}
_GENERIC_SEMANTIC_WORDS = {
    "ability", "activate", "activated", "add", "card", "cards", "choose", "discard",
    "draw", "exchange", "gain", "hand", "letter", "letters", "lot", "lots", "page",
    "pages", "player", "players", "put", "record", "redeem", "resolve", "resolved",
    "return", "reveal", "sheol", "shuffle", "spend", "tower", "type", "types",
    "your", "their", "from", "into", "onto", "then", "that", "this", "with", "when",
    "where", "which", "while", "what", "have", "has", "are", "and", "the", "for",
    "one", "two", "three", "four", "five", "any", "all", "may", "must", "can",
}

_CANONICAL_TERM_LOOKUP = {term.casefold(): term for term in CANONICAL_RULE_TERMS}
_BANNED_FRAGMENTS = (
    "your deck",
    "their deck",
    "the deck",
    "a deck",
    "discard pile",
    "graveyard",
    "battlefield",
    "mana",
    "hit point",
    "life total",
    "tap ",
    "untap",
    "cast ",
    "counter target",
    "exile ",
    "banish ",
    "mill ",
    "tutor ",
    "scry ",
    "sacrifice ",
    "destroy ",
    "bounce ",
    "flicker ",
    "buff ",
    "debuff ",
)


ABILITY_RULES_CONTEXT = """GAME MECHANICS AND CLOSED VOCABULARY:
- There is one shared 90-card draw pile, the Tower. Never say "your deck" or "their deck".
- A player may have cards in hand and face-up Pages. Sheol is the shared face-up discard pile. Resolve holds an activated card and its cost until the ability finishes.
- A Lot is a 5-, 6-, or 7-card type-composition recipe. The Chapter Lot is shared; each player also has a Portion Lot. Recording the Chapter Lot creates a Page (a face-up scored set); Recording any Portion Lot sends the cards to Sheol and earns Letters, never a Page.
- Pages exist only within the current Chapter and are cleared at Chapter reset; abilities that reference Pages see only Pages created this Chapter.
- Letters pay for Hand Activations (1 Letter each) and are worth 3 points each at Chapter scoring. Wreaths award points for Recording the Chapter Lot first or closing the Chapter.
- Activating the revealed card costs 0 Letters; activating from hand costs 1 Letter; both pay the printed rarity cost (COMMON 0, UNCOMMON 0, RARE 1, GLORIOUS 2 discards).
- Draw means take from the Tower. Discard means move from hand to Sheol unless the copy explicitly names another legal origin.
- Card types are NOUN, VERB, ADJECTIVE, NAME, and TITLE. Stats are LORE, CONTEXT, and COMPLEXITY.
- TITLE may stand for NOUN or NAME only when recorded, at most one substitution per Record.
- An activated card and its activation-cost discards go to Sheol and cannot be redeemed. Do not restate or replace that base rule in an ability.
- Generated copy begins "When this ability resolves," so its trigger and timing are explicit without restating the activation cost.
- Legal rules actions are: draw, discard, reveal, look at, put, add, return, shuffle, choose, exchange, gain, spend, record, activate, redeem, and name.
- Flavor words are not rules actions. Never turn a card word or semantic anchor into an imperative label, a colon heading, or invented shorthand (for example, "Sink").
- Every action must explicitly identify its actor or target, affected quantity, relevant source and destination zones, condition, duration, and outcome wherever those operands apply.
- Draw copy names the Tower as its source. Card movement names both the cards and their destination. Ongoing copy states its duration. Conditional copy states both the condition and result.
- Avoid bare pronouns such as it, them, they, "that many," or "the other"; repeat the player, card, quantity, or zone instead.
"""


def rarity_budget(rarity: str) -> dict:
    """Return an isolated copy of the explicit budget for ``rarity``."""
    rarity_key = str(rarity).strip().upper()
    if rarity_key not in RARITY_BUDGETS:
        raise ValueError(f"Unknown rarity: {rarity}")
    return deepcopy(RARITY_BUDGETS[rarity_key])


def _normalize_identity(word: str, card_type: str, rarity: str | None = None) -> tuple[str, str, str | None]:
    word_key = str(word).strip().upper()
    type_key = str(card_type).strip().upper()
    rarity_key = str(rarity).strip().upper() if rarity is not None else None
    if not word_key:
        raise ValueError("word is required")
    if type_key not in CARD_TYPES:
        raise ValueError(f"Unknown card type: {card_type}")
    if rarity_key is not None and rarity_key not in RARITIES:
        raise ValueError(f"Unknown rarity: {rarity}")
    return word_key, type_key, rarity_key


def _parse_json_response(raw: str) -> dict:
    text = str(raw).strip()
    candidates = [text]
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 3:
            fenced = parts[1].lstrip()
            if fenced.lower().startswith("json"):
                fenced = fenced[4:].lstrip("\r\n ")
            candidates.append(fenced.strip())
    left = text.find("{")
    right = text.rfind("}")
    if left >= 0 and right > left:
        candidates.append(text[left:right + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict):
            return value
    raise AbilityGenerationError("Model response did not contain a JSON object.")


def build_semantic_prompt(word: str, card_type: str, *, gloss: str = "") -> str:
    """Build the first-stage prompt, which has no target-rarity input."""
    word_key, type_key, _ = _normalize_identity(word, card_type)
    gloss_line = f"\nCanonical gloss: {gloss.strip()}" if str(gloss).strip() else ""
    return (
        "Derive the semantic identity for a Hypertext word card before any game-power shaping.\n"
        f"Word: {word_key}\n"
        f"Grammatical card type: {type_key}{gloss_line}\n"
        f"Type lens: {TYPE_SEMANTIC_ROLES[type_key]}\n\n"
        "Return ONLY JSON with this shape:\n"
        "{\n"
        '  "core_meaning": "one precise sentence",\n'
        '  "type_expression": "how that grammatical identity should feel mechanically",\n'
        '  "mechanical_anchors": ["three to five short words or phrases that could appear verbatim in rules copy"],\n'
        '  "mechanic_seed": "a rules-agnostic physical or conceptual transformation"\n'
        "}\n"
        "Keep the anchors distinct and concrete. Do not propose final rules copy or name a power tier."
    )


def _validate_semantic_seed(seed: dict) -> list[str]:
    issues: list[str] = []
    for key in ("core_meaning", "type_expression", "mechanic_seed"):
        if not isinstance(seed.get(key), str) or not seed[key].strip():
            issues.append(f"semantic seed requires non-empty {key}")
    anchors = seed.get("mechanical_anchors")
    if not isinstance(anchors, list) or not 3 <= len(anchors) <= 5:
        issues.append("semantic seed requires three to five mechanical_anchors")
    elif any(not isinstance(anchor, str) or not anchor.strip() for anchor in anchors):
        issues.append("every mechanical anchor must be a non-empty string")
    if "rarity" in seed:
        issues.append("semantic seed must be derived before and without a rarity field")
    return issues


def _budget_prompt(rarity: str) -> str:
    budget = rarity_budget(rarity)
    lines = [f"{rarity} intent: {budget['intent']}"]
    for dimension in DIMENSIONS:
        bounds = budget["dimensions"][dimension]
        scale = "; ".join(f"{rating}={meaning}" for rating, meaning in RATING_SCALE[dimension].items())
        lines.append(
            f"- {dimension}: allowed {bounds['min']}..{bounds['max']}; shared scale: {scale}"
        )
    lines.append(f"- total of five ratings: allowed {budget['total']['min']}..{budget['total']['max']}")
    return "\n".join(lines)


def build_candidate_prompt(
    word: str,
    card_type: str,
    rarity: str,
    semantic_seed: dict,
    *,
    feedback: list[str] | None = None,
) -> str:
    """Build the second-stage prompt that shapes a fixed semantic seed."""
    word_key, type_key, rarity_key = _normalize_identity(word, card_type, rarity)
    feedback_text = ""
    if feedback:
        feedback_text = (
            "\nA prior candidate was rejected. Correct every issue without changing the semantic seed:\n- "
            + "\n- ".join(str(issue) for issue in feedback)
            + "\n"
        )
    return (
        "Turn the already-derived semantic seed into one legal Hypertext ability. "
        "Do not replace the seed with a generic effect. Apply the target budget only after choosing how the seed maps to mechanics. "
        "The card word is flavor, never an invented rules action.\n\n"
        f"Word: {word_key}\nCard type: {type_key}\nTarget rarity: {rarity_key}\n"
        f"Semantic seed (authoritative):\n{json.dumps(semantic_seed, ensure_ascii=False, indent=2)}\n\n"
        f"Exact rarity budget:\n{_budget_prompt(rarity_key)}\n\n"
        + ABILITY_RULES_CONTEXT
        + feedback_text
        + "\nReturn ONLY JSON with this shape:\n"
        "{\n"
        '  "mechanical_expression": "how the seed becomes this exact game-state change",\n'
        '  "semantic_anchor": "one mechanical_anchors value copied exactly and explained in mechanical_expression; do not print it as an action label",\n'
        '  "semantic_evidence": ["two or more exact excerpts from ability_text whose relationships embody the seed without an invented action"],\n'
        '  "ability_text": "one or two sentences, at most 60 words, beginning exactly When this ability resolves,",\n'
        '  "rules_terms": ["every canonical game term used in ability_text"],\n'
        '  "rules_actions": ["every legal rules action used in ability_text, in resolution order"],\n'
        '  "clarity": {\n'
        '    "trigger": "exact printed trigger excerpt",\n'
        '    "timing": "exact printed timing excerpt",\n'
        '    "targets": ["exact printed actor or target excerpts"],\n'
        '    "zones": ["every canonical zone named in the copy"],\n'
        '    "quantities": ["exact printed quantity excerpts"],\n'
        '    "duration": "instantaneous, or an exact printed duration excerpt",\n'
        '    "condition": "none, or an exact printed condition excerpt",\n'
        '    "outcomes": ["exact printed state-change excerpts"]\n'
        "  },\n"
        '  "rarity_budget": {\n'
        '    "scope": {"rating": 0, "rationale": "truthful reason"},\n'
        '    "complexity": {"rating": 0, "rationale": "truthful reason"},\n'
        '    "setup": {"rating": 0, "rationale": "truthful reason"},\n'
        '    "interaction": {"rating": 0, "rationale": "truthful reason"},\n'
        '    "payoff": {"rating": 0, "rationale": "truthful reason"}\n'
        "  }\n"
        "}\n"
        "Every clarity excerpt other than the literals instantaneous and none must occur verbatim in ability_text. "
        "Ratings must describe the printed copy, not the designer's intention. Do not add reminder text for the base activation cost."
    )


def _declared_terms(candidate: dict) -> tuple[list[str], list[str]]:
    raw_terms = candidate.get("rules_terms")
    if not isinstance(raw_terms, list):
        return [], ["rules_terms must be a list"]
    terms: list[str] = []
    issues: list[str] = []
    for raw in raw_terms:
        if not isinstance(raw, str) or not raw.strip():
            issues.append("every rules_terms entry must be a non-empty string")
            continue
        key = raw.strip().casefold()
        canonical = _CANONICAL_TERM_LOOKUP.get(key)
        if canonical is None:
            issues.append(f"undefined rules term declared: {raw.strip()}")
            continue
        if canonical not in terms:
            terms.append(canonical)
    return terms, issues


def _excerpt_in_text(excerpt: str, text: str) -> bool:
    value = str(excerpt).strip()
    if not value:
        return False
    return re.search(rf"(?<!\w){re.escape(value)}(?!\w)", text, re.IGNORECASE) is not None


def _semantic_tokens(value: str) -> set[str]:
    return {
        token.casefold()
        for token in re.findall(r"\b[\w'-]{3,}\b", str(value), flags=re.UNICODE)
        if token.casefold() not in _GENERIC_SEMANTIC_WORDS
    }


def _validate_semantic_evidence(
    candidate: dict,
    semantic_seed: dict,
    ability_text: str,
    selected_anchor: str,
) -> list[str]:
    issues: list[str] = []
    expression = candidate.get("mechanical_expression")
    if isinstance(expression, str) and selected_anchor and not _excerpt_in_text(selected_anchor, expression):
        issues.append("mechanical_expression must explicitly explain the selected semantic_anchor")

    raw_evidence = candidate.get("semantic_evidence")
    if not isinstance(raw_evidence, list) or len(raw_evidence) < 2:
        return issues + ["semantic_evidence requires at least two exact ability_text excerpts"]
    evidence: list[str] = []
    for raw in raw_evidence:
        if not isinstance(raw, str) or not raw.strip():
            issues.append("every semantic_evidence entry must be a non-empty string")
            continue
        excerpt = raw.strip()
        if not _excerpt_in_text(excerpt, ability_text):
            issues.append(f"semantic_evidence is not printed verbatim: {excerpt}")
        if excerpt.casefold() not in {item.casefold() for item in evidence}:
            evidence.append(excerpt)
    if len(evidence) < 2:
        issues.append("semantic_evidence must contain two distinct excerpts")

    seed_text = " ".join(
        str(value)
        for value in (
            semantic_seed.get("core_meaning", ""),
            semantic_seed.get("type_expression", ""),
            semantic_seed.get("mechanic_seed", ""),
            " ".join(str(item) for item in semantic_seed.get("mechanical_anchors", [])),
        )
    )
    seed_tokens = _semantic_tokens(seed_text)
    evidence_tokens = _semantic_tokens(" ".join(evidence))
    anchor_tokens = _semantic_tokens(selected_anchor)
    causal_overlap = (seed_tokens & evidence_tokens) - anchor_tokens
    if len(causal_overlap) < 2:
        issues.append(
            "weak flavor: printed semantic evidence must share at least two non-rules concepts "
            "with the semantic seed beyond the selected anchor"
        )
    return issues


def _zones_in_copy(text: str) -> list[str]:
    canonical = {zone.casefold(): zone for zone in CANONICAL_ZONES}
    zones: list[str] = []
    for match in _ZONE_PATTERN.finditer(text):
        key = match.group(0).casefold()
        zone = canonical.get(key)
        if zone and zone not in zones:
            zones.append(zone)
    return zones


def _validate_clarity(candidate: dict, ability_text: str) -> tuple[list[str], dict[str, bool]]:
    issues: list[str] = []
    checks: dict[str, bool] = {}
    clarity = candidate.get("clarity")
    required = ("trigger", "timing", "targets", "zones", "quantities", "duration", "condition", "outcomes")
    if not isinstance(clarity, dict):
        return ["clarity must be an object with every operand audit field"], {
            "clarity_audit_complete": False,
            "clarity_excerpts_are_printed": False,
        }

    missing = [field for field in required if field not in clarity]
    checks["clarity_audit_complete"] = not missing
    if missing:
        issues.append("clarity is missing fields: " + ", ".join(missing))

    excerpts_are_printed = True
    for field in ("trigger", "timing"):
        value = clarity.get(field)
        if not isinstance(value, str) or not value.strip():
            issues.append(f"clarity.{field} must be a non-empty exact excerpt")
            excerpts_are_printed = False
        elif not _excerpt_in_text(value, ability_text):
            issues.append(f"clarity.{field} is not printed verbatim")
            excerpts_are_printed = False

    for field in ("targets", "quantities", "outcomes"):
        values = clarity.get(field)
        if not isinstance(values, list) or not values:
            issues.append(f"clarity.{field} must contain at least one exact excerpt")
            excerpts_are_printed = False
            continue
        for value in values:
            if not isinstance(value, str) or not value.strip() or not _excerpt_in_text(value, ability_text):
                issues.append(f"clarity.{field} contains an excerpt not printed verbatim: {value}")
                excerpts_are_printed = False

    declared_zones = clarity.get("zones")
    canonical_zone_lookup = {zone.casefold(): zone for zone in CANONICAL_ZONES}
    normalized_zones: list[str] = []
    if not isinstance(declared_zones, list):
        issues.append("clarity.zones must be a list")
    else:
        for raw in declared_zones:
            if not isinstance(raw, str) or raw.strip().casefold() not in canonical_zone_lookup:
                issues.append(f"clarity.zones contains an undefined zone: {raw}")
                continue
            zone = canonical_zone_lookup[raw.strip().casefold()]
            if zone not in normalized_zones:
                normalized_zones.append(zone)
    printed_zones = _zones_in_copy(ability_text)
    if set(normalized_zones) != set(printed_zones):
        issues.append(
            "clarity.zones must exactly match printed zones; "
            f"declared={normalized_zones}, printed={printed_zones}"
        )

    duration = clarity.get("duration")
    if not isinstance(duration, str) or not duration.strip():
        issues.append("clarity.duration must be instantaneous or an exact printed duration")
    elif duration.strip().casefold() == "instantaneous":
        if _ONGOING_PATTERN.search(ability_text):
            issues.append("ongoing copy requires an explicit printed duration")
    elif not _excerpt_in_text(duration, ability_text):
        issues.append("clarity.duration is not printed verbatim")

    condition = clarity.get("condition")
    condition_present = _CONDITION_PATTERN.search(ability_text) is not None
    if not isinstance(condition, str) or not condition.strip():
        issues.append("clarity.condition must be none or an exact printed condition")
    elif condition.strip().casefold() == "none":
        if condition_present:
            issues.append("conditional copy requires the printed condition in clarity.condition")
    elif not _excerpt_in_text(condition, ability_text):
        issues.append("clarity.condition is not printed verbatim")
    elif not condition_present:
        issues.append("clarity.condition declares a condition that the copy does not express")

    checks["clarity_excerpts_are_printed"] = excerpts_are_printed
    checks["explicit_resolution_timing"] = ability_text.casefold().startswith(
        "when this ability resolves,"
    )
    if not checks["explicit_resolution_timing"]:
        issues.append('ability_text must begin exactly "When this ability resolves,"')
    checks["no_colon_action_labels"] = ":" not in ability_text
    if not checks["no_colon_action_labels"]:
        issues.append("colon action labels are forbidden; use only established rules actions")

    ambiguous = sorted({match.group(0) for match in _AMBIGUOUS_REFERENCES.finditer(ability_text)})
    checks["no_ambiguous_references"] = not ambiguous
    if ambiguous:
        issues.append("ambiguous shorthand or antecedent: " + ", ".join(ambiguous))

    body = re.sub(r"^when this ability resolves,\s*", "", ability_text, flags=re.IGNORECASE)
    checks["explicit_initial_actor"] = re.match(
        r"^(?:you\b|each player\b|every player\b|all players\b|target player\b|the chosen player\b)",
        body,
        re.IGNORECASE,
    ) is not None
    if not checks["explicit_initial_actor"]:
        issues.append("the first resolution step must explicitly name its actor or target")
    implicit_then = re.search(
        r"\bthen\s+(?!(?:you\b|each player\b|every player\b|all players\b|target player\b|"
        r"the chosen player\b|each of you\b))",
        ability_text,
        re.IGNORECASE,
    )
    checks["every_then_step_has_actor"] = implicit_then is None
    if implicit_then:
        issues.append("every step after then must explicitly name its actor or target")
    return issues, checks


def _action_occurrences(text: str) -> list[tuple[int, int, str]]:
    occurrences: list[tuple[int, int, str]] = []
    for action, pattern in _ACTION_PATTERNS.items():
        for match in pattern.finditer(text):
            occurrences.append((match.start(), match.end(), action))
    occurrences.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    deduplicated: list[tuple[int, int, str]] = []
    for item in occurrences:
        if deduplicated and item[0] < deduplicated[-1][1]:
            continue
        deduplicated.append(item)
    return deduplicated


def _validate_rules_actions(candidate: dict, ability_text: str) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    raw_actions = candidate.get("rules_actions")
    if not isinstance(raw_actions, list):
        raw_actions = []
        issues.append("rules_actions must be a list in resolution order")
    declared: list[str] = []
    for raw in raw_actions:
        if not isinstance(raw, str) or not raw.strip():
            issues.append("every rules_actions entry must be a non-empty string")
            continue
        action = raw.strip().casefold()
        if action not in CANONICAL_RULE_ACTIONS:
            issues.append(f"undefined rules action declared: {raw.strip()}")
            continue
        declared.append(action)
    detected = [item[2] for item in _action_occurrences(ability_text)]
    if declared != detected:
        issues.append(
            "rules_actions must exactly match printed legal actions in resolution order; "
            f"declared={declared}, printed={detected}"
        )

    action_heads = {action.split()[0] for action in CANONICAL_RULE_ACTIONS}
    head_matches = list(_ACTOR_ACTION_PATTERN.finditer(ability_text))
    head_matches.extend(_CONDITIONED_PLAYER_ACTION_PATTERN.finditer(ability_text))
    undefined_heads: list[str] = []
    for match in sorted(head_matches, key=lambda item: item.start()):
        head = match.group("head").casefold()
        if head in _NON_ACTION_HEADS:
            continue
        if head not in action_heads and head.removesuffix("s") not in action_heads:
            if head not in undefined_heads:
                undefined_heads.append(head)
    for head in undefined_heads:
        issues.append(f"undefined action label or shorthand: {head}")
    return issues, detected


def _action_segments(text: str) -> list[tuple[str, str]]:
    occurrences = _action_occurrences(text)
    segments: list[tuple[str, str]] = []
    for index, (start, _end, action) in enumerate(occurrences):
        finish = occurrences[index + 1][0] if index + 1 < len(occurrences) else len(text)
        segment = re.split(r"[.;]", text[start:finish], maxsplit=1)[0]
        segments.append((action, segment.strip(" ,")))
    return segments


def _validate_action_operands(ability_text: str) -> list[str]:
    issues: list[str] = []
    for action, segment in _action_segments(ability_text):
        has_quantity = _QUANTITY_PATTERN.search(segment) is not None
        has_object = _CARD_OR_RESOURCE_PATTERN.search(segment) is not None
        zones = _zones_in_copy(segment)
        if action in {"draw", "discard", "reveal", "look at", "put", "add", "return", "choose"}:
            if not has_quantity:
                issues.append(f"{action} is missing an explicit quantity: {segment}")
            if not has_object:
                issues.append(f"{action} is missing an explicit affected object: {segment}")
        if action == "draw" and "Tower" not in zones:
            issues.append(f"draw is missing the explicit Tower source: {segment}")
        elif action == "discard" and not {"hand", "Sheol"}.issubset(set(zones)):
            issues.append(f"discard must explicitly state hand as source and Sheol as destination: {segment}")
        elif action in {"reveal", "look at"} and not zones:
            issues.append(f"{action} is missing an explicit source zone: {segment}")
        elif action == "put" and not re.search(
            r"\b(?:on|onto|into|to)\b[^.;]{0,60}"
            r"\b(?:Tower|hand|Pages|Sheol|Chapter Lot|Lots?|Lot)\b",
            segment,
            re.IGNORECASE,
        ):
            issues.append(f"put is missing an explicit destination zone: {segment}")
        elif action == "add" and not any(zone in {"hand", "Pages"} for zone in zones):
            issues.append(f"add is missing an explicit hand or Pages destination: {segment}")
        elif action == "return" and len(zones) < 2:
            issues.append(f"return must explicitly state both source and destination zones: {segment}")
        elif action == "shuffle" and ("Tower" not in zones or not has_object):
            issues.append(f"shuffle must explicitly state what enters the Tower: {segment}")
        elif action == "choose" and "card" in segment.casefold() and not zones:
            issues.append(f"choose cards is missing an explicit source zone: {segment}")
        elif action == "exchange" and not re.search(r"\b(?:Lot|Lots|card|cards|Letter|Letters)\b", segment, re.IGNORECASE):
            issues.append(f"exchange is missing the two exchanged objects: {segment}")
        elif action in {"gain", "spend"}:
            if not has_quantity or not re.search(r"\b(?:Letter|Letters|Wreath|Wreaths)\b", segment, re.IGNORECASE):
                issues.append(f"{action} is missing an explicit resource and quantity: {segment}")
        elif action in {"record", "activate", "redeem"} and not has_object:
            issues.append(f"{action} is missing an explicit affected card or Lot: {segment}")
        elif action == "name" and not re.search(r"\bcard type\b", segment, re.IGNORECASE):
            issues.append(f"name must explicitly identify a card type: {segment}")
    return issues


def _estimate_printed_ratings(ability_text: str, actions: list[str]) -> dict[str, int]:
    lower = ability_text.casefold()
    zones = _zones_in_copy(ability_text)
    global_players = re.search(r"\b(?:each|every|all) players?\b", lower) is not None
    another_player = re.search(r"\b(?:other|chosen|target|another) player\b", lower) is not None

    if global_players:
        scope = 3
    elif another_player or len(zones) >= 2:
        scope = 2
    else:
        scope = 1 if actions else 0

    complexity = min(3, len(actions)) if actions else 0
    if _CONDITION_PATTERN.search(ability_text):
        complexity = max(2, complexity)
    if global_players:
        complexity = 3

    setup = 0
    if _CONDITION_PATTERN.search(ability_text) or any(zone in {"Pages", "Sheol"} for zone in zones):
        setup = 1
    if re.search(
        r"\b(?:at least|at most|fewer than|more than)\s+\d+\s+cards?\s+(?:in|from)\s+(?:Pages|Sheol)\b",
        ability_text,
        re.IGNORECASE,
    ):
        setup = 2

    if global_players:
        interaction = 3
    elif another_player:
        if re.search(r"\b(?:exchange|Lot|Lots|discard|from (?:the )?(?:chosen|other|target) player's hand)\b", ability_text, re.IGNORECASE):
            interaction = 2
        else:
            interaction = 1
    else:
        interaction = 0

    payoff = 1 if actions else 0
    if global_players and ("hand" in lower or "draw" in actions):
        payoff = 3
    elif "exchange" in actions and "gain" in actions:
        payoff = 3
    elif re.search(r"\b(?:adds?|draws?|returns?)\s+(?:up to\s+|exactly\s+)?(?:[2-9]|\d{2,})\b", ability_text, re.IGNORECASE):
        payoff = 3
    elif re.search(r"\bgains?\s+(?:[2-9]|\d{2,})\s+Letters?\b", ability_text, re.IGNORECASE):
        payoff = 3
    else:
        material_actions = [
            action for action in actions if action not in {"choose", "reveal", "look at", "name"}
        ]
        if len(material_actions) >= 2:
            payoff = 2
        elif "gain" in material_actions:
            payoff = 2
    return {
        "scope": scope,
        "complexity": complexity,
        "setup": setup,
        "interaction": interaction,
        "payoff": payoff,
    }


def validate_ability_candidate(candidate: dict, semantic_seed: dict, rarity: str) -> dict:
    """Deterministically validate structure, vocabulary, and rarity ratings."""
    rarity_key = str(rarity).strip().upper()
    budget = rarity_budget(rarity_key)
    issues: list[str] = []
    checks: dict[str, bool] = {}

    ability_text = candidate.get("ability_text")
    text_ok = isinstance(ability_text, str) and bool(ability_text.strip())
    checks["ability_text_present"] = text_ok
    if not text_ok:
        issues.append("ability_text must be a non-empty string")
        ability_text = ""
    else:
        ability_text = ability_text.strip()

    word_count = len(re.findall(r"\b[\w'-]+\b", ability_text, flags=re.UNICODE))
    checks["copy_within_60_words"] = bool(ability_text) and word_count <= 60
    if ability_text and word_count > 60:
        issues.append(f"ability_text has {word_count} words; maximum is 60")
    sentence_count = len(re.findall(r"[.!?]+(?:\s|$)", ability_text))
    if ability_text and sentence_count == 0:
        sentence_count = 1
    checks["copy_within_two_sentences"] = bool(ability_text) and sentence_count <= 2
    if ability_text and sentence_count > 2:
        issues.append("ability_text must contain at most two sentences")

    anchors = semantic_seed.get("mechanical_anchors", [])
    anchor_lookup = {
        str(anchor).strip().casefold(): str(anchor).strip()
        for anchor in anchors
        if isinstance(anchor, str) and anchor.strip()
    }
    selected_anchor = str(candidate.get("semantic_anchor", "")).strip()
    anchor_is_seeded = selected_anchor.casefold() in anchor_lookup
    checks["semantic_anchor_from_seed"] = anchor_is_seeded
    if not anchor_is_seeded:
        issues.append("semantic_anchor must exactly match one semantic seed anchor")

    mechanical_expression = candidate.get("mechanical_expression")
    checks["mechanical_expression_present"] = isinstance(mechanical_expression, str) and bool(mechanical_expression.strip())
    if not checks["mechanical_expression_present"]:
        issues.append("mechanical_expression must explain the semantic game-state mapping")
    semantic_issues = _validate_semantic_evidence(
        candidate,
        semantic_seed,
        ability_text,
        selected_anchor,
    )
    issues.extend(semantic_issues)
    checks["semantic_evidence_is_strong"] = not semantic_issues

    terms, term_issues = _declared_terms(candidate)
    issues.extend(term_issues)
    checks["declared_terms_are_canonical"] = not term_issues
    missing_terms = [term for term in terms if term.casefold() not in ability_text.casefold()]
    checks["declared_terms_appear_in_copy"] = not missing_terms
    if missing_terms:
        issues.append("declared rules terms missing from ability_text: " + ", ".join(missing_terms))

    lower_copy = ability_text.casefold()
    banned = [fragment.strip() for fragment in _BANNED_FRAGMENTS if fragment in lower_copy]
    checks["closed_vocabulary_has_no_banned_terms"] = not banned
    if banned:
        issues.append("noncanonical rules vocabulary: " + ", ".join(banned))

    clarity_issues, clarity_checks = _validate_clarity(candidate, ability_text)
    issues.extend(clarity_issues)
    checks.update(clarity_checks)

    action_issues, detected_actions = _validate_rules_actions(candidate, ability_text)
    issues.extend(action_issues)
    checks["only_established_rules_actions"] = not action_issues
    operand_issues = _validate_action_operands(ability_text)
    issues.extend(operand_issues)
    checks["all_action_operands_explicit"] = not operand_issues

    ratings: dict[str, int] = {}
    budget_value = candidate.get("rarity_budget")
    if not isinstance(budget_value, dict):
        issues.append("rarity_budget must be an object")
        budget_value = {}
    for dimension in DIMENSIONS:
        entry = budget_value.get(dimension)
        valid_entry = isinstance(entry, dict)
        if not valid_entry:
            issues.append(f"rarity_budget.{dimension} must be an object")
            continue
        rating = entry.get("rating")
        rationale = entry.get("rationale")
        if isinstance(rating, bool) or not isinstance(rating, int):
            issues.append(f"rarity_budget.{dimension}.rating must be an integer")
            continue
        ratings[dimension] = rating
        if not isinstance(rationale, str) or not rationale.strip():
            issues.append(f"rarity_budget.{dimension}.rationale is required")
        bounds = budget["dimensions"][dimension]
        if not bounds["min"] <= rating <= bounds["max"]:
            issues.append(
                f"{dimension} rating {rating} is outside {rarity_key} range "
                f"{bounds['min']}..{bounds['max']}"
            )

    all_dimensions = len(ratings) == len(DIMENSIONS)
    checks["all_five_budget_dimensions_present"] = all_dimensions
    total = sum(ratings.values()) if all_dimensions else None
    total_ok = (
        total is not None
        and budget["total"]["min"] <= total <= budget["total"]["max"]
    )
    checks["budget_total_in_range"] = total_ok
    if total is not None and not total_ok:
        issues.append(
            f"budget total {total} is outside {rarity_key} range "
            f"{budget['total']['min']}..{budget['total']['max']}"
        )

    printed_ratings = _estimate_printed_ratings(ability_text, detected_actions)
    rating_mismatches: list[str] = []
    if all_dimensions:
        for dimension in DIMENSIONS:
            declared = ratings[dimension]
            printed = printed_ratings[dimension]
            if declared != printed:
                rating_mismatches.append(
                    f"rarity mismatch: {dimension} rating {declared} does not match printed effect rating {printed}"
                )
            bounds = budget["dimensions"][dimension]
            if not bounds["min"] <= printed <= bounds["max"]:
                rating_mismatches.append(
                    f"rarity mismatch: printed {dimension} rating {printed} is outside {rarity_key} range "
                    f"{bounds['min']}..{bounds['max']}"
                )
    issues.extend(rating_mismatches)
    checks["printed_effect_matches_declared_rarity"] = not rating_mismatches

    return {
        "passed": not issues,
        "rarity": rarity_key,
        "ratings": ratings,
        "printed_rating_estimate": printed_ratings,
        "total": total,
        "budget": budget,
        "checks": checks,
        "issues": issues,
    }


def build_critic_prompt(
    word: str,
    card_type: str,
    rarity: str,
    semantic_seed: dict,
    candidate: dict,
) -> str:
    """Build a fresh, adversarial critic prompt for an otherwise valid candidate."""
    word_key, type_key, rarity_key = _normalize_identity(word, card_type, rarity)
    return (
        "You are the independent Hypertext ability critic. The candidate is untrusted. "
        "Judge only the printed ability; do not trust its audits or rationales. "
        "Reject weak flavor when the state change does not causally embody the word and type. "
        "Reject any invented action label, undefined shorthand, foreign game term, missing operand, ambiguous antecedent, "
        "unstated condition or duration, or rating that overstates or understates the printed effect. "
        "Do not rewrite the ability.\n\n"
        f"Word: {word_key}\nCard type: {type_key}\nRarity: {rarity_key}\n"
        f"Semantic seed:\n{json.dumps(semantic_seed, ensure_ascii=False, indent=2)}\n"
        f"Candidate:\n{json.dumps(candidate, ensure_ascii=False, indent=2)}\n\n"
        f"Budget and scale:\n{_budget_prompt(rarity_key)}\n\n"
        + ABILITY_RULES_CONTEXT
        + "\nReturn ONLY JSON with this exact shape:\n"
        "{\n"
        '  "thematic_fidelity": {"pass": true, "reason": "specific causal connection"},\n'
        '  "type_fidelity": {"pass": true, "reason": "grammatical identity is embodied"},\n'
        '  "flavor_strength": {"pass": true, "reason": "mechanics carry the flavor without a label"},\n'
        '  "rarity_fit": {"pass": true, "reason": "ratings are truthful and effect earns its tier"},\n'
        '  "rules_legality": {"pass": true, "reason": "only established terms and actions are used"},\n'
        '  "operand_completeness": {"pass": true, "reason": "trigger, timing, target, zones, quantities, duration, condition, and outcomes are explicit wherever applicable"},\n'
        '  "rules_clarity": {"pass": true, "reason": "order and references have one first-read interpretation"},\n'
        '  "overall_pass": true,\n'
        '  "issues": []\n'
        "}\n"
        "overall_pass must be true only when every category passes and issues is empty."
    )


def validate_critic_result(critic: dict) -> dict:
    """Validate the independent critic's verdict without trusting overall_pass."""
    issues: list[str] = []
    category_passes: dict[str, bool] = {}
    for category in CRITIC_CATEGORIES:
        entry = critic.get(category)
        passed = isinstance(entry, dict) and entry.get("pass") is True
        reason_ok = isinstance(entry, dict) and isinstance(entry.get("reason"), str) and bool(entry["reason"].strip())
        category_passes[category] = passed and reason_ok
        if not passed:
            issues.append(f"critic rejected {category}")
        elif not reason_ok:
            issues.append(f"critic omitted reason for {category}")
    critic_issues = critic.get("issues")
    if not isinstance(critic_issues, list):
        issues.append("critic issues must be a list")
        critic_issues = []
    else:
        issues.extend(str(issue).strip() for issue in critic_issues if str(issue).strip())
    if critic.get("overall_pass") is not True:
        issues.append("critic overall_pass is false")
    if critic.get("overall_pass") is True and not all(category_passes.values()):
        issues.append("critic overall_pass contradicts category results")
    return {
        "passed": not issues and all(category_passes.values()),
        "category_passes": category_passes,
        "issues": issues,
    }


def generate_validated_ability(
    *,
    word: str,
    card_type: str,
    rarity: str,
    generate: Callable[..., str],
    gloss: str = "",
    max_attempts: int = 3,
) -> dict:
    """Generate semantic seed, budgeted ability, and an independent verdict."""
    word_key, type_key, rarity_key = _normalize_identity(word, card_type, rarity)
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    semantic_prompt = build_semantic_prompt(word_key, type_key, gloss=gloss)
    semantic_raw = generate(semantic_prompt, temperature=0.2, use_google_search=False)
    semantic_seed = _parse_json_response(semantic_raw)
    semantic_issues = _validate_semantic_seed(semantic_seed)
    if semantic_issues:
        raise AbilityGenerationError("Invalid semantic seed: " + "; ".join(semantic_issues))

    attempts: list[dict] = []
    feedback: list[str] = []
    for attempt_number in range(1, max_attempts + 1):
        candidate_prompt = build_candidate_prompt(
            word_key,
            type_key,
            rarity_key,
            semantic_seed,
            feedback=feedback,
        )
        candidate_raw = generate(candidate_prompt, temperature=0.6, use_google_search=False)
        attempt_record: dict = {
            "attempt": attempt_number,
            "candidate_prompt": candidate_prompt,
        }
        try:
            candidate = _parse_json_response(candidate_raw)
        except AbilityGenerationError as exc:
            feedback = [str(exc)]
            attempt_record["candidate_parse_error"] = str(exc)
            attempts.append(attempt_record)
            continue

        deterministic = validate_ability_candidate(candidate, semantic_seed, rarity_key)
        attempt_record["candidate"] = candidate
        attempt_record["deterministic_validation"] = deterministic
        if not deterministic["passed"]:
            feedback = list(deterministic["issues"])
            attempts.append(attempt_record)
            continue

        critic_prompt = build_critic_prompt(word_key, type_key, rarity_key, semantic_seed, candidate)
        critic_raw = generate(critic_prompt, temperature=0.0, use_google_search=False)
        attempt_record["critic_prompt"] = critic_prompt
        try:
            critic = _parse_json_response(critic_raw)
        except AbilityGenerationError as exc:
            feedback = [str(exc)]
            attempt_record["critic_parse_error"] = str(exc)
            attempts.append(attempt_record)
            continue
        critic_validation = validate_critic_result(critic)
        attempt_record["critic"] = critic
        attempt_record["critic_validation"] = critic_validation
        attempts.append(attempt_record)
        if not critic_validation["passed"]:
            feedback = list(critic_validation["issues"])
            continue

        return {
            "version": "semantic-rarity-clarity-v2",
            "word": word_key,
            "card_type": type_key,
            "rarity": rarity_key,
            "semantic_prompt": semantic_prompt,
            "semantic_seed": semantic_seed,
            "rarity_budget": rarity_budget(rarity_key),
            "attempts": attempts,
            "selected_attempt": attempt_number,
            "ability_text": candidate["ability_text"].strip(),
            "candidate": candidate,
            "deterministic_validation": deterministic,
            "critic": critic,
            "critic_validation": critic_validation,
        }

    detail = "; ".join(feedback) if feedback else "no candidate passed"
    raise AbilityGenerationError(
        f"No validated {rarity_key} ability for {word_key}/{type_key} after {max_attempts} attempts: {detail}"
    )
