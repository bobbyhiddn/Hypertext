import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest

from hypertext.cards import abilities
from hypertext.cards.abilities import (
    AbilityGenerationError,
    CRITIC_CATEGORIES,
    DIMENSIONS,
    RARITY_BUDGETS,
    build_candidate_prompt,
    build_critic_prompt,
    build_semantic_prompt,
    generate_validated_ability,
    rarity_budget,
    validate_ability_candidate,
    validate_critic_result,
)
from hypertext.pipeline import daily


PROOF_ROOT = Path(__file__).resolve().parents[2] / "operator_review" / "req-ppaug-034-ability-generator-proof"


def semantic_seed():
    return {
        "core_meaning": "To inspect the hidden top object until its exact identity becomes visible.",
        "type_expression": "A VERB should perform a precise change from hidden to visible information.",
        "mechanical_anchors": ["survey", "bring into view", "witness"],
        "mechanic_seed": "Exactly one hidden object at the top becomes visible.",
    }


def _ratings(values):
    return {
        dimension: {"rating": rating, "rationale": f"The printed copy has {dimension} rating {rating}."}
        for dimension, rating in zip(DIMENSIONS, values)
    }


def candidate_for(*, ability_text=None):
    return {
        "mechanical_expression": "The survey makes exactly one hidden top card visible.",
        "semantic_anchor": "survey",
        "semantic_evidence": ["exactly 1 card", "top of the Tower"],
        "ability_text": ability_text
        or (
            "You reveal exactly 1 card from the top of the Tower, "
            "then add that revealed card to your hand."
        ),
        "rules_terms": ["reveal", "card", "Tower", "add", "hand"],
        "rules_actions": ["reveal", "add"],
        "clarity": {
            "trigger": "activation",
            "timing": "instantaneous",
            "targets": ["you"],
            "zones": ["Tower", "hand"],
            "quantities": ["exactly 1 card"],
            "duration": "instantaneous",
            "condition": "none",
            "outcomes": [
                "reveal exactly 1 card from the top of the Tower",
                "add that revealed card to your hand",
            ],
        },
        "rarity_budget": _ratings([2, 2, 0, 0, 1]),
    }


def passing_critic():
    reasons = {
        "thematic_fidelity": "The hidden top card becomes visible through inspection.",
        "type_fidelity": "The VERB performs a visible state change.",
        "flavor_strength": "The relationship carries the meaning without using survey as a rules action.",
        "rarity_fit": "The one-step information effect and ratings fit Common.",
        "rules_legality": "Every action and game term is established in Hypertext.",
        "operand_completeness": "Trigger, actor, quantity, source, timing, and outcome are explicit.",
        "rules_clarity": "The single step has one first-read interpretation.",
        "power_floor": "A selective reveal taken into hand beats a plain draw by a modest margin.",
    }
    return {
        category: {"pass": True, "reason": reasons[category]}
        for category in CRITIC_CATEGORIES
    } | {"overall_pass": True, "issues": []}


def test_every_rarity_has_an_explicit_five_dimension_budget():
    assert set(RARITY_BUDGETS) == {"COMMON", "UNCOMMON", "RARE", "GLORIOUS"}
    for rarity, budget in RARITY_BUDGETS.items():
        assert tuple(budget["dimensions"]) == DIMENSIONS
        assert budget["total"]["min"] <= budget["total"]["max"]
        assert rarity_budget(rarity) == budget
        assert rarity_budget(rarity) is not budget


def test_semantic_prompt_is_built_without_a_target_rarity_or_budget():
    prompt = build_semantic_prompt("BUILD", "VERB", gloss="to construct")
    assert "Word: BUILD" in prompt
    assert "Grammatical card type: VERB" in prompt
    assert "Target rarity" not in prompt
    assert "Exact rarity budget" not in prompt


def test_candidate_and_critic_prompts_demand_first_read_clarity_and_legality():
    candidate_prompt = build_candidate_prompt("SEE", "VERB", "COMMON", semantic_seed())
    for phrase in (
        "",
        "Flavor words are not rules actions",
        "trigger",
        "targets",
        "zones",
        "quantities",
        "duration",
        "condition",
        "outcomes",
        "rules_actions",
    ):
        assert phrase in candidate_prompt

    critic_prompt = build_critic_prompt("SEE", "VERB", "COMMON", semantic_seed(), candidate_for())
    for category in CRITIC_CATEGORIES:
        assert f'"{category}"' in critic_prompt
    assert "undefined shorthand" in critic_prompt
    assert "missing operand" in critic_prompt


def test_deterministic_validation_accepts_explicit_budgeted_copy_and_rejects_over_budget_copy():
    valid = validate_ability_candidate(candidate_for(), semantic_seed(), "COMMON")
    assert valid["passed"] is True, valid["issues"]
    assert valid["total"] == 5
    assert valid["printed_rating_estimate"] == {
        "scope": 2,
        "complexity": 1,
        "setup": 0,
        "interaction": 0,
        "payoff": 1,
    }

    over_budget = candidate_for()
    over_budget["rarity_budget"]["interaction"]["rating"] = 1
    invalid = validate_ability_candidate(over_budget, semantic_seed(), "COMMON")
    assert invalid["passed"] is False
    assert any("interaction rating 1" in issue for issue in invalid["issues"])


def test_deterministic_validation_rejects_ambiguity_and_missing_operands():
    ambiguous = candidate_for(
        ability_text=(
            "You reveal exactly 2 cards from the top of the Tower, "
            "then put them on the bottom of the Tower."
        )
    )
    ambiguous["rules_actions"] = ["reveal", "put"]
    ambiguous["clarity"]["quantities"] = ["exactly 2 cards"]
    ambiguous["clarity"]["outcomes"] = ["put them on the bottom of the Tower"]
    report = validate_ability_candidate(ambiguous, semantic_seed(), "UNCOMMON")
    assert report["passed"] is False
    assert any("ambiguous shorthand or antecedent" in issue for issue in report["issues"])
    # imperative continuation after "then" is legal active voice now

    missing = candidate_for(ability_text="You put cards.")
    missing["rules_terms"] = ["ability", "resolve", "put", "cards"]
    missing["rules_actions"] = ["put"]
    missing["clarity"]["zones"] = []
    missing["clarity"]["quantities"] = ["cards"]
    missing["clarity"]["outcomes"] = ["put cards"]
    report = validate_ability_candidate(missing, semantic_seed(), "COMMON")
    assert report["passed"] is False
    assert any("put is missing an explicit quantity" in issue for issue in report["issues"])
    assert any("put is missing an explicit destination zone" in issue for issue in report["issues"])

    source_only = candidate_for(
        ability_text="You put exactly 1 card from your hand."
    )
    source_only["rules_terms"] = ["ability", "resolve", "put", "card", "hand"]
    source_only["rules_actions"] = ["put"]
    source_only["clarity"]["zones"] = ["hand"]
    source_only["clarity"]["quantities"] = ["exactly 1 card"]
    source_only["clarity"]["outcomes"] = ["put exactly 1 card from your hand"]
    report = validate_ability_candidate(source_only, semantic_seed(), "COMMON")
    assert report["passed"] is False
    assert any("put is missing an explicit destination zone" in issue for issue in report["issues"])


def test_deterministic_validation_rejects_undefined_shorthand_and_illegal_terms():
    shorthand = candidate_for(
        ability_text=(
            "You sink exactly 1 card from the top of the Tower "
            "to the bottom of the Tower."
        )
    )
    shorthand["rules_actions"] = []
    shorthand["clarity"]["outcomes"] = ["sink exactly 1 card from the top of the Tower"]
    report = validate_ability_candidate(shorthand, semantic_seed(), "COMMON")
    assert report["passed"] is False
    assert "undefined action label or shorthand: sink" in report["issues"]

    conditional_shorthand = candidate_for(
        ability_text=(
            " if you have exactly 1 card in hand, you sink exactly 1 card "
            "from the top of the Tower to the bottom of the Tower."
        )
    )
    conditional_shorthand["rules_actions"] = []
    conditional_shorthand["clarity"]["zones"] = ["hand", "Tower"]
    conditional_shorthand["clarity"]["quantities"] = ["exactly 1 card"]
    conditional_shorthand["clarity"]["condition"] = "if you have exactly 1 card in hand"
    conditional_shorthand["clarity"]["outcomes"] = [
        "sink exactly 1 card from the top of the Tower to the bottom of the Tower"
    ]
    report = validate_ability_candidate(conditional_shorthand, semantic_seed(), "COMMON")
    assert report["passed"] is False
    assert "undefined action label or shorthand: sink" in report["issues"]

    illegal = candidate_for(
        ability_text=(
            "You return exactly 1 card from your graveyard to your hand."
        )
    )
    illegal["rules_terms"] = ["ability", "resolve", "return", "card", "hand"]
    illegal["rules_actions"] = ["return"]
    illegal["clarity"]["zones"] = ["hand"]
    illegal["clarity"]["outcomes"] = ["return exactly 1 card from your graveyard to your hand"]
    report = validate_ability_candidate(illegal, semantic_seed(), "COMMON")
    assert report["passed"] is False
    assert any("graveyard" in issue for issue in report["issues"])


def test_deterministic_validation_rejects_anchor_only_weak_flavor():
    generic = candidate_for(
        ability_text="You draw exactly 1 card from the Tower."
    )
    generic["mechanical_expression"] = "The survey is asserted as a label for a generic draw."
    generic["semantic_evidence"] = ["draw exactly 1 card", "from the Tower"]
    generic["rules_terms"] = ["ability", "resolve", "draw", "card", "Tower"]
    generic["rules_actions"] = ["draw"]
    generic["clarity"]["quantities"] = ["exactly 1 card"]
    generic["clarity"]["outcomes"] = ["draw exactly 1 card from the Tower"]
    report = validate_ability_candidate(generic, semantic_seed(), "COMMON")
    assert report["passed"] is False
    assert any("weak flavor" in issue for issue in report["issues"])


def test_deterministic_validation_rejects_forged_rarity_ratings():
    forged = candidate_for()
    forged["rarity_budget"] = _ratings([3, 3, 1, 3, 3])
    report = validate_ability_candidate(forged, semantic_seed(), "GLORIOUS")
    assert report["passed"] is False
    assert report["printed_rating_estimate"]["scope"] == 2
    assert any("rarity mismatch" in issue for issue in report["issues"])
    assert any("outside GLORIOUS range" in issue for issue in report["issues"])


def test_independent_critic_requires_every_adversarial_category():
    critic = passing_critic()
    critic["rarity_fit"]["pass"] = False
    report = validate_critic_result(critic)
    assert report["passed"] is False
    assert "critic rejected rarity_fit" in report["issues"]
    assert "critic overall_pass contradicts category results" in report["issues"]

    missing_legality = passing_critic()
    del missing_legality["rules_legality"]
    report = validate_critic_result(missing_legality)
    assert report["passed"] is False
    assert "critic rejected rules_legality" in report["issues"]


def test_generator_calls_semantics_then_budgeted_candidate_then_independent_critic():
    calls = []

    def fake_generate(prompt, **kwargs):
        calls.append((prompt, kwargs))
        if prompt.startswith("Derive the semantic identity"):
            return json.dumps(semantic_seed())
        if prompt.startswith("Turn the already-derived semantic seed"):
            return json.dumps(candidate_for())
        if prompt.startswith("You are the independent Hypertext ability critic"):
            return json.dumps(passing_critic())
        raise AssertionError("unexpected prompt")

    result = generate_validated_ability(
        word="SEE",
        card_type="VERB",
        rarity="COMMON",
        generate=fake_generate,
    )
    assert not result["ability_text"].casefold().startswith("when this ability resolves")
    assert result["version"] == "semantic-rarity-clarity-v2"
    assert result["selected_attempt"] == 1
    assert [call[0].splitlines()[0] for call in calls] == [
        "Derive the semantic identity for a Hypertext word card before any game-power shaping.",
        (
            "Turn the already-derived semantic seed into one legal Hypertext ability. "
            "Do not replace the seed with a generic effect. Apply the target budget only after choosing how the seed maps to mechanics. "
            "The card word is flavor, never an invented rules action."
        ),
        (
            "You are the independent Hypertext ability critic. The candidate is untrusted. "
            "Judge only the printed ability; do not trust its audits or rationales. "
            "Reject weak flavor when the state change does not causally embody the word and type. "
            "Reject any invented action label, undefined shorthand, foreign game term, missing operand, ambiguous antecedent, "
            "unstated condition or duration, or rating that overstates or understates the printed effect. "
            "Apply the draw-one baseline: fail power_floor when a rational player would usually rather have a plain "
            '"Draw one card from the Tower." than this ability, and also fail it when a COMMON beats that baseline '
            "by more than one modest kicker. "
            "Do not rewrite the ability."
        ),
    ]
    assert calls[0][1]["temperature"] == 0.2
    assert calls[2][1]["temperature"] == 0.0


def test_generator_retries_after_critic_rejection_and_records_both_attempts():
    candidate_calls = 0
    critic_calls = 0

    def fake_generate(prompt, **_kwargs):
        nonlocal candidate_calls, critic_calls
        if prompt.startswith("Derive the semantic identity"):
            return json.dumps(semantic_seed())
        if prompt.startswith("Turn the already-derived semantic seed"):
            candidate_calls += 1
            return json.dumps(candidate_for())
        critic_calls += 1
        verdict = passing_critic()
        if critic_calls == 1:
            verdict["flavor_strength"] = {"pass": False, "reason": "The effect is too generic."}
            verdict["overall_pass"] = False
            verdict["issues"] = ["Make the semantic cause mechanically specific."]
        return json.dumps(verdict)

    result = generate_validated_ability(
        word="SEE",
        card_type="VERB",
        rarity="COMMON",
        generate=fake_generate,
    )
    assert result["selected_attempt"] == 2
    assert candidate_calls == 2
    assert critic_calls == 2
    assert result["attempts"][0]["critic_validation"]["passed"] is False
    assert result["attempts"][1]["critic_validation"]["passed"] is True


def test_generator_fails_closed_when_no_candidate_passes():
    invalid = candidate_for()
    invalid["semantic_anchor"] = "not seeded"

    def fake_generate(prompt, **_kwargs):
        if prompt.startswith("Derive the semantic identity"):
            return json.dumps(semantic_seed())
        return json.dumps(invalid)

    with pytest.raises(AbilityGenerationError, match="No validated"):
        generate_validated_ability(
            word="SEE",
            card_type="VERB",
            rarity="COMMON",
            generate=fake_generate,
            max_attempts=2,
        )


def test_generator_has_no_named_card_exceptions():
    source = inspect.getsource(abilities)
    for word in ("BUILD", "SCATTER", "STONE", "NATION", "ARK", "COVENANT"):
        assert f'"{word}"' not in source
        assert f"'{word}'" not in source


def test_exact_six_proof_replays_through_the_corrected_generator():
    records_path = PROOF_ROOT / "generation-records.json"
    producer_path = PROOF_ROOT / "producer-cards.json"
    if not records_path.exists() or not producer_path.exists():
        pytest.skip("REQ-PPAUG-034 proof packet is generated later in this change")

    packet = json.loads(records_path.read_text(encoding="utf-8"))
    producer = json.loads(producer_path.read_text(encoding="utf-8"))
    live_packet = json.loads((PROOF_ROOT / "live-critic-results.json").read_text(encoding="utf-8"))
    live_by_id = {item["id"]: item for item in live_packet["results"]}
    expected = [
        ("BUILD", "VERB", "RARE"),
        ("SCATTER", "VERB", "GLORIOUS"),
        ("STONE", "NOUN", "COMMON"),
        ("NATION", "NOUN", "UNCOMMON"),
        ("ARK", "NOUN", "RARE"),
        ("COVENANT", "NOUN", "GLORIOUS"),
    ]
    assert [(item["word"], item["card_type"], item["rarity"]) for item in packet["records"]] == expected
    assert len(producer["cards"]) == 6

    for record, card in zip(packet["records"], producer["cards"]):
        saved = record["generation"]

        def replay(prompt, **_kwargs):
            if prompt.startswith("Derive the semantic identity"):
                return json.dumps(saved["semantic_seed"])
            if prompt.startswith("Turn the already-derived semantic seed"):
                return json.dumps(saved["candidate"])
            if prompt.startswith("You are the independent Hypertext ability critic"):
                return json.dumps(saved["critic"])
            raise AssertionError("unexpected replay prompt")

        regenerated = generate_validated_ability(
            word=record["word"],
            card_type=record["card_type"],
            rarity=record["rarity"],
            gloss=record["gloss"],
            generate=replay,
        )
        assert regenerated == saved
        assert regenerated["ability_text"] == card["content"]["ABILITY_TEXT"]
        assert saved["attempts"][0]["critic_prompt"] == live_by_id[record["id"]]["critic_prompt"]
        assert saved["critic"] == live_by_id[record["id"]]["critic"]
        assert live_by_id[record["id"]]["critic_validation"]["passed"] is True


def test_exact_six_producer_records_preserve_prior_card_schema_shape():
    producer_path = PROOF_ROOT / "producer-cards.json"
    if not producer_path.exists():
        pytest.skip("REQ-PPAUG-034 proof packet is generated later in this change")
    previous_path = PROOF_ROOT.parent / "6801a192-ability-generator-proof" / "producer-cards.json"
    current = json.loads(producer_path.read_text(encoding="utf-8"))["cards"]
    previous = json.loads(previous_path.read_text(encoding="utf-8"))["cards"]
    assert len(current) == len(previous) == 6
    for current_card, previous_card in zip(current, previous):
        current_without_copy = deepcopy(current_card)
        previous_without_copy = deepcopy(previous_card)
        current_without_copy["content"].pop("ABILITY_TEXT")
        previous_without_copy["content"].pop("ABILITY_TEXT")
        assert current_without_copy == previous_without_copy


def test_daily_recipe_preserves_validated_copy_against_research_rewrite(monkeypatch):
    generated = {
        "ability_text": "You reveal exactly 1 card from the top of the Tower.",
        "version": "semantic-rarity-clarity-v2",
    }
    monkeypatch.setattr(daily, "generate_validated_ability", lambda **_kwargs: generated)
    monkeypatch.setattr(daily, "_load_rules_appendix", lambda: "")
    monkeypatch.setattr(
        daily,
        "generate_text_with_grounding",
        lambda *_args, **_kwargs: (json.dumps({"ability_text": "MODEL REWROTE THIS"}), {"queries": [], "sources": []}),
    )
    recipe = daily._generate_card_recipe(
        number=9,
        word="SEE",
        card_type="VERB",
        rarity="COMMON",
    )
    assert recipe["ability_text"] == generated["ability_text"]
    assert recipe["ability_generation"] is generated


def test_daily_recipe_keeps_queue_supplied_ability_as_exact_legacy_override(monkeypatch):
    monkeypatch.setattr(
        daily,
        "generate_validated_ability",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("override must bypass generator")),
    )
    monkeypatch.setattr(daily, "_load_rules_appendix", lambda: "")
    monkeypatch.setattr(
        daily,
        "generate_text_with_grounding",
        lambda *_args, **_kwargs: (json.dumps({}), {}),
    )
    recipe = daily._generate_card_recipe(
        number=1,
        word="GRACE",
        card_type="NOUN",
        rarity="COMMON",
        ability="Draw 1 card.",
    )
    assert recipe["ability_text"] == "Draw 1 card."
    assert "ability_generation" not in recipe
