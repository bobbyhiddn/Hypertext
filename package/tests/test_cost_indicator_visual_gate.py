"""Full-resolution regressions for the structured +CARD visual contract."""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import tempfile
import unittest
from pathlib import Path

from click.testing import CliRunner
from PIL import Image, ImageDraw

from hypertext.cards.cost_indicator_gate import inspect_cost_indicator
from hypertext.cli import cli
from hypertext.pipeline import daily


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "cost_indicator_visual_cases.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
RECIPE_TEMPLATE = json.loads(
    (ROOT / "templates" / "card_prompt_template_explicit.json").read_text(
        encoding="utf-8"
    )
)
MANIFEST = json.loads(
    (
        ROOT
        / "templates"
        / "card"
        / "v001"
        / "composed"
        / "manifest.json"
    ).read_text(encoding="utf-8")
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _template(card_type: str, rarity: str) -> Path:
    return (
        ROOT
        / "templates"
        / "card"
        / "v001"
        / "composed"
        / card_type.lower()
        / rarity.lower()
        / "template_1024x1536.png"
    )


def _recipe(card_type: str, rarity: str) -> dict:
    recipe = copy.deepcopy(RECIPE_TEMPLATE)
    recipe["content"].update(
        {
            "CARD_TYPE": card_type,
            "RARITY_TEXT": rarity,
            "RARITY_ICON": rarity,
        }
    )
    return recipe


def _resized(path: Path) -> Image.Image:
    with Image.open(path) as source:
        return source.convert("RGB").resize(
            tuple(FIXTURE["reference_size"]), Image.Resampling.LANCZOS
        )


def _replace_with_common_background(
    image: Image.Image,
    *,
    card_type: str,
    box: tuple[int, int, int, int],
) -> None:
    common = _resized(_template(card_type, "COMMON"))
    image.paste(common.crop(box), box[:2])


def _make_candidate(
    path: Path,
    *,
    card_type: str = "VERB",
    rarity: str = "RARE",
    mutation: str | None = None,
) -> None:
    image = _resized(_template(card_type, rarity))
    region = tuple(FIXTURE["cost_region"])
    mutations = FIXTURE["mutations"]

    if mutation == "forbidden-card-label":
        style = mutations["build_forbidden_card_label"]
        center_x, center_y = style["center"]
        half_width, half_height = style["half_width"], style["half_height"]
        ImageDraw.Draw(image).polygon(
            (
                (center_x, center_y - half_height),
                (center_x + half_width, center_y),
                (center_x, center_y + half_height),
                (center_x - half_width, center_y),
            ),
            fill=tuple(style["fill_rgb"]),
        )
    elif mutation == "missing-plus":
        box = tuple(mutations["rare_plus_patch"])
        _replace_with_common_background(image, card_type=card_type, box=box)
    elif mutation == "missing-indicator":
        _replace_with_common_background(image, card_type=card_type, box=region)
    elif mutation == "wrong-value":
        glorious = _resized(_template(card_type, "GLORIOUS"))
        _replace_with_common_background(image, card_type=card_type, box=region)
        image.paste(glorious.crop(region), region[:2])
    elif mutation == "duplicated-card":
        source_box = tuple(mutations["rare_card_patch"])
        destination = tuple(mutations["duplicate_card_destination"])
        image.paste(image.crop(source_box), destination)
    elif mutation == "displaced":
        indicator = image.crop(region)
        _replace_with_common_background(image, card_type=card_type, box=region)
        dx, dy = mutations["displacement"]
        image.paste(indicator, (region[0] + dx, region[1] + dy))
    elif mutation == "malformed-plus":
        box = tuple(mutations["rare_plus_patch"])
        _replace_with_common_background(image, card_type=card_type, box=box)
        draw = ImageDraw.Draw(image)
        draw.rectangle((873, 127, 902, 133), fill=(39, 34, 43))
    elif mutation == "extra-on-common":
        rare = _resized(_template(card_type, "RARE"))
        image.paste(rare.crop(region), region[:2])
    elif mutation is not None:
        raise AssertionError(f"unknown cost-indicator mutation: {mutation}")
    image.save(path, format="PNG")


class CostIndicatorVisualGateTests(unittest.TestCase):
    def inspect_fixture(
        self,
        mutation: str | None = None,
        *,
        card_type: str = "VERB",
        rarity: str = "RARE",
        recipe: dict | None = None,
    ) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate.png"
            _make_candidate(
                candidate,
                card_type=card_type,
                rarity=rarity,
                mutation=mutation,
            )
            template = _template(card_type, rarity)
            return inspect_cost_indicator(
                candidate,
                template,
                recipe or _recipe(card_type, rarity),
                expected_template_sha256=_digest(template),
            )

    def test_all_twenty_hash_verified_template_cells_define_the_expected_cost(self):
        self.assertEqual(len(MANIFEST["outputs"]), 20)
        with tempfile.TemporaryDirectory() as directory:
            for index, item in enumerate(MANIFEST["outputs"]):
                with self.subTest(card_type=item["type"], rarity=item["rarity"]):
                    template = ROOT / item["path"]
                    candidate = Path(directory) / f"candidate-{index}.png"
                    _make_candidate(
                        candidate,
                        card_type=item["type"],
                        rarity=item["rarity"],
                    )
                    report = inspect_cost_indicator(
                        candidate,
                        template,
                        _recipe(item["type"], item["rarity"]),
                        expected_template_sha256=item["sha256"],
                    )
                    self.assertTrue(report["passed"], report["defects"])
                    self.assertEqual(report["template"]["sha256"], item["sha256"])

    def test_build_forbidden_diamond_inside_card_face_is_rejected(self):
        report = self.inspect_fixture("forbidden-card-label")
        self.assertFalse(report["passed"])
        self.assertIn(
            "cost-card-label-or-face-mismatch",
            {item["code"] for item in report["defects"]},
        )

    def test_wrong_value_missing_plus_omission_and_duplication_are_rejected(self):
        expected = {
            "wrong-value": "cost-card-count-mismatch",
            "missing-plus": "cost-plus-sign-count-mismatch",
            "missing-indicator": "cost-card-count-mismatch",
            "duplicated-card": "cost-card-count-mismatch",
            "malformed-plus": "cost-plus-sign-count-mismatch",
        }
        for mutation, defect in expected.items():
            with self.subTest(mutation=mutation):
                report = self.inspect_fixture(mutation)
                self.assertFalse(report["passed"])
                self.assertIn(defect, {item["code"] for item in report["defects"]})

    def test_displacement_and_forbidden_common_indicator_are_rejected(self):
        displaced = self.inspect_fixture("displaced")
        self.assertFalse(displaced["passed"])
        self.assertIn(
            "cost-indicator-placement-mismatch",
            {item["code"] for item in displaced["defects"]},
        )

        common = self.inspect_fixture(
            "extra-on-common", rarity="COMMON"
        )
        self.assertFalse(common["passed"])
        self.assertIn(
            "cost-card-count-mismatch",
            {item["code"] for item in common["defects"]},
        )

    def test_structured_recipe_value_and_placement_must_be_canonical(self):
        recipe = _recipe("VERB", "RARE")
        indicator = recipe["style_guide"]["iconography"]["cost_indicator"]
        indicator["placement"] = "beside_rarity"
        indicator["costs"]["RARE"]["display"] = "+" + "\U0001f0a0" * 2
        report = self.inspect_fixture(recipe=recipe)
        self.assertFalse(report["passed"])
        codes = {item["code"] for item in report["defects"]}
        self.assertIn("cost-recipe-placement-mismatch", codes)
        self.assertIn("cost-recipe-value-mismatch", codes)

    def test_installed_cli_fails_closed_and_persists_the_cost_rejection(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as directory:
            card_dir = Path(directory) / "card"
            outputs = card_dir / "outputs"
            outputs.mkdir(parents=True)
            recipe = _recipe("VERB", "RARE")
            recipe["content"].update(
                {"STAT_LORE": 0, "STAT_CONTEXT": 0, "STAT_COMPLEXITY": 0}
            )
            (card_dir / "card.json").write_text(
                json.dumps(recipe), encoding="utf-8"
            )
            _make_candidate(
                outputs / "card_1024x1536.png",
                mutation="forbidden-card-label",
            )

            result = runner.invoke(cli, ["visual-gate", "--card-dir", str(card_dir)])
            self.assertNotEqual(result.exit_code, 0)
            report = json.loads(
                (outputs / "visual-gate.json").read_text(encoding="utf-8")
            )
            self.assertFalse(report["passed"])
            self.assertTrue(report["stat_pips"]["passed"])
            self.assertFalse(report["cost_indicator"]["passed"])
            self.assertIn(
                "cost-card-label-or-face-mismatch",
                {item["code"] for item in report["cost_indicator"]["defects"]},
            )

    def test_supported_generate_revise_rebuild_grade_and_review_paths_share_gate(self):
        self.assertIs(daily._run_stat_pip_visual_gate, daily._run_card_visual_gate)
        routed = {
            "generate": daily._generate_image_for_card_dir,
            "revise": daily.phase_revise,
            "rebuild": daily.phase_rebuild,
            "grade": daily.phase_grade,
            "review": daily.phase_review,
        }
        for name, function in routed.items():
            with self.subTest(path=name):
                self.assertIn(
                    "_run_stat_pip_visual_gate(", inspect.getsource(function)
                )

    def test_rejected_build_evidence_fails_and_plain_build_evidence_passes(self):
        evidence = FIXTURE["evidence"]
        missing = [
            path
            for item in evidence.values()
            for path in (item["candidate"], item["card"])
            if not Path(path).is_file()
        ]
        if missing:
            self.skipTest("external BUILD evidence unavailable: " + ", ".join(missing))

        rejected = evidence["rejected_build"]
        rejected_report = inspect_cost_indicator(
            rejected["candidate"],
            ROOT / rejected["template"],
            json.loads(Path(rejected["card"]).read_text(encoding="utf-8")),
            expected_template_sha256=_digest(ROOT / rejected["template"]),
        )
        self.assertFalse(rejected_report["passed"])
        self.assertIn(
            rejected["expected_defect"],
            {item["code"] for item in rejected_report["defects"]},
        )

        accepted = evidence["accepted_plain_build"]
        accepted_report = inspect_cost_indicator(
            accepted["candidate"],
            ROOT / accepted["template"],
            json.loads(Path(accepted["card"]).read_text(encoding="utf-8")),
            expected_template_sha256=_digest(ROOT / accepted["template"]),
        )
        self.assertTrue(accepted_report["passed"], accepted_report["defects"])


if __name__ == "__main__":
    unittest.main()
