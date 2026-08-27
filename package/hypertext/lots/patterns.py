"""Gameplay evaluator and feasibility model for typed Lot recipes."""
from __future__ import annotations
from itertools import permutations
from math import comb
from typing import Any, Mapping

CARD_TYPES = ("NOUN", "VERB", "ADJECTIVE", "NAME", "TITLE")
WILD_TARGETS = ("NOUN", "NAME")  # TITLE may stand for these, at most once per Record
DECK = {"NOUN": 16, "VERB": 20, "ADJECTIVE": 20, "NAME": 16, "TITLE": 18}
HAND = 7


def _counts(hand: Mapping[str, int]) -> dict[str, int]:
    return {t: int(hand.get(t, 0)) for t in CARD_TYPES}


def _fixed_ok(hand: dict[str, int], need: dict[str, int]) -> bool:
    def fits(nd: dict[str, int], spare_title: int) -> bool:
        return (all(hand[t] >= nd.get(t, 0) for t in CARD_TYPES)
                and hand["TITLE"] >= nd.get("TITLE", 0) + spare_title)
    if fits(need, 0):
        return True
    for target in WILD_TARGETS:
        if need.get(target, 0) > 0:
            nd = dict(need); nd[target] -= 1
            if fits(nd, 1):
                return True
    return False


def _groups_ok(hand: dict[str, int], groups: list[dict[str, Any]]) -> bool:
    sized = [g for g in groups if g["constraint"] != "any"]
    any_needed = sum(g["count"] for g in groups) - sum(g["count"] for g in sized)
    for perm in permutations(CARD_TYPES, len(sized)):
        for wild_into in (None, *WILD_TARGETS):
            used, ok, wild_used = {}, True, 0
            for g, t in zip(sized, perm):
                need = g["count"] - (1 if wild_into == t else 0)
                if wild_into == t:
                    wild_used += 1
                if hand[t] - used.get(t, 0) < need:
                    ok = False
                    break
                used[t] = used.get(t, 0) + need
            if not ok or wild_used > 1:
                continue
            if wild_used and hand["TITLE"] - used.get("TITLE", 0) < wild_used:
                continue
            used["TITLE"] = used.get("TITLE", 0) + wild_used
            remaining = sum(hand.values()) - sum(used.values())
            if remaining >= any_needed:
                return True
    return False


def _all5pair_ok(hand: dict[str, int]) -> bool:
    for wild_into in (None, *WILD_TARGETS):
        need = {t: 1 for t in CARD_TYPES}
        if wild_into:
            need[wild_into] -= 1
            need["TITLE"] += 1
        if not all(hand[t] >= need[t] for t in CARD_TYPES):
            continue
        rest = {t: hand[t] - need[t] for t in CARD_TYPES}
        if any(v >= 2 for v in rest.values()):
            return True
    return False


def satisfies(recipe: dict[str, Any], hand: Mapping[str, int]) -> bool:
    """True when `hand` (type -> count) contains a legal Record for `recipe`."""
    counts = _counts(hand)
    kind = recipe.get("kind")
    if kind == "fixed":
        need: dict[str, int] = {}
        for t in recipe["composition"]:
            need[t] = need.get(t, 0) + 1
        return _fixed_ok(counts, need)
    if kind == "groups":
        return _groups_ok(counts, list(recipe["groups"]))
    if kind == "all_types_plus_pair":
        return _all5pair_ok(counts)
    raise ValueError(f"unknown recipe kind {kind!r}")


def opening_hand_probability(recipe: dict[str, Any], deck: Mapping[str, int] = DECK,
                             hand_size: int = HAND) -> float:
    """P(a fresh hand of `hand_size` from `deck` already holds a legal Record)."""
    total = sum(deck.values())
    denom = comb(total, hand_size)
    prob = 0.0
    types = list(deck)
    def rec(i: int, remaining: int, ways: int, counts: dict[str, int]) -> None:
        nonlocal prob
        if i == len(types) - 1:
            t = types[i]
            if remaining <= deck[t]:
                counts[t] = remaining
                if satisfies(recipe, counts):
                    prob += ways * comb(deck[t], remaining) / denom
            return
        t = types[i]
        for k in range(min(deck[t], remaining) + 1):
            counts[t] = k
            rec(i + 1, remaining - k, ways * comb(deck[t], k), counts)
    rec(0, hand_size, 1, {})
    return prob
