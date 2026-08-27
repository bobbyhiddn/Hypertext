"""Deterministic regressions for template-relative full-card stat pip QA."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner
from PIL import Image, ImageDraw

from hypertext.cards.stat_pip_gate import inspect_stat_pips
from hypertext.cli import cli
from hypertext.pipeline.daily import _apply_validated_stat_pip_counts


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "stat_pip_visual_cases.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
TEMPLATE = (
    ROOT
    / "templates"
    / "card"
    / "v001"
    / "composed"
    / "noun"
    / "rare"
    / "template_1024x1536.png"
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ellipse(draw: ImageDraw.ImageDraw, x: int, y: int, radius: int, color: list[int]) -> None:
    draw.ellipse(
        (x - radius, y - radius, x + radius, y + radius),
        fill=tuple(color),
    )


def _make_candidate(
    path: Path,
    defect: str | None = None,
    *,
    template: Path = TEMPLATE,
) -> None:
    """Build a full-resolution fixture without changing the canonical template."""
    width, height = FIXTURE["reference_size"]
    with Image.open(template) as source:
        image = source.convert("RGB").resize(
            (width, height), Image.Resampling.LANCZOS
        )
    draw = ImageDraw.Draw(image)
    row_y = FIXTURE["row_y"]
    counts = FIXTURE["expected_counts"]
    solid = FIXTURE["styles"]["correct_solid_filled"]
    for row, expected_count in zip(FIXTURE["row_x"], counts, strict=True):
        for x in row[:expected_count]:
            _ellipse(draw, x, row_y, solid["radius"], solid["fill_rgb"])

    if defect == "concentric":
        style = FIXTURE["styles"]["concentric_filled_defect"]
        x = FIXTURE["row_x"][0][0]
        _ellipse(draw, x, row_y, style["outer_radius"], style["outer_rgb"])
        _ellipse(draw, x, row_y, style["middle_radius"], style["middle_rgb"])
        _ellipse(draw, x, row_y, style["core_radius"], style["core_rgb"])
    elif defect == "wrong-dark-fill":
        style = FIXTURE["styles"]["wrong_dark_filled_defect"]
        x = FIXTURE["row_x"][0][0]
        _ellipse(draw, x, row_y, style["radius"], style["fill_rgb"])
    elif defect == "pale-gold-empty":
        style = FIXTURE["styles"]["pale_gold_empty_defect"]
        x = FIXTURE["row_x"][0][4]
        _ellipse(draw, x, row_y, style["outer_radius"], style["outline_rgb"])
        _ellipse(draw, x, row_y, style["inner_radius"], style["interior_rgb"])
    elif defect is not None:
        raise AssertionError(f"unknown fixture defect: {defect}")
    image.save(path, format="PNG")


class TemplateRelativeStatPipGateTests(unittest.TestCase):
    def inspect_fixture(self, defect: str | None = None):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate.png"
            _make_candidate(candidate, defect)
            return inspect_stat_pips(
                candidate,
                TEMPLATE,
                FIXTURE["expected_counts"],
            )

    def test_correct_solid_fills_and_exact_template_empty_outlines_pass(self):
        before = _digest(TEMPLATE)
        report = self.inspect_fixture()
        self.assertTrue(report["passed"])
        self.assertEqual(report["defects"], [])
        self.assertEqual(tuple(report["observed_counts"].values()), (3, 2, 4))
        self.assertEqual(_digest(TEMPLATE), before)

    def test_validated_gate_counts_replace_vision_guess_before_scoring(self):
        description = SimpleNamespace(
            stat_lore=1,
            stat_context=1,
            stat_complexity=1,
        )
        expected, observed = _apply_validated_stat_pip_counts(
            description,
            {
                "STAT_LORE": 4,
                "STAT_CONTEXT": 5,
                "STAT_COMPLEXITY": 1,
            },
            {
                "observed_counts": {
                    "STAT_LORE": 4,
                    "STAT_CONTEXT": 5,
                    "STAT_COMPLEXITY": 1,
                }
            },
        )

        self.assertEqual(expected, (4, 5, 1))
        self.assertEqual(observed, (4, 5, 1))
        self.assertEqual(
            (
                description.stat_lore,
                description.stat_context,
                description.stat_complexity,
            ),
            (4, 5, 1),
        )

    def test_correct_pips_pass_against_all_twenty_immutable_template_cells(self):
        manifest_path = ROOT / "templates" / "card" / "v001" / "composed" / "manifest.json"
        outputs = json.loads(manifest_path.read_text(encoding="utf-8"))["outputs"]
        self.assertEqual(len(outputs), 20)
        before = {
            item["path"]: _digest(ROOT / item["path"])
            for item in outputs
        }
        with tempfile.TemporaryDirectory() as directory:
            for index, item in enumerate(outputs):
                with self.subTest(card_type=item["type"], rarity=item["rarity"]):
                    template = ROOT / item["path"]
                    candidate = Path(directory) / f"candidate-{index}.png"
                    _make_candidate(candidate, template=template)
                    report = inspect_stat_pips(
                        candidate,
                        template,
                        FIXTURE["expected_counts"],
                    )
                    self.assertTrue(report["passed"], report["defects"])
                    self.assertEqual(_digest(template), item["sha256"])
        self.assertEqual(
            before,
            {item["path"]: _digest(ROOT / item["path"]) for item in outputs},
        )

    def test_concentric_filled_pip_fails_even_when_count_is_correct(self):
        report = self.inspect_fixture("concentric")
        self.assertFalse(report["passed"])
        self.assertEqual(tuple(report["observed_counts"].values()), (3, 2, 4))
        self.assertIn(
            "filled-concentric-or-nonuniform",
            {item["code"] for item in report["defects"]},
        )

    def test_solid_dark_fill_with_wrong_template_color_fails(self):
        report = self.inspect_fixture("wrong-dark-fill")
        self.assertFalse(report["passed"])
        self.assertEqual(tuple(report["observed_counts"].values()), (3, 2, 4))
        self.assertIn(
            "filled-fill-style-mismatch",
            {item["code"] for item in report["defects"]},
        )

    def test_pale_gold_empty_outline_fails_even_when_count_is_correct(self):
        report = self.inspect_fixture("pale-gold-empty")
        self.assertFalse(report["passed"])
        self.assertEqual(tuple(report["observed_counts"].values()), (3, 2, 4))
        self.assertIn(
            "empty-outline-style-mismatch",
            {item["code"] for item in report["defects"]},
        )

    def test_rejected_full_resolution_proof_outputs_trigger_exact_regressions(self):
        missing = [
            item["path"]
            for item in FIXTURE["evidence"].values()
            if not Path(item["path"]).is_file()
        ]
        if missing:
            self.skipTest("external rejection evidence unavailable: " + ", ".join(missing))

        for name, item in FIXTURE.get("registration_rescued", {}).items():
            if not Path(item["path"]).is_file():
                continue
            with self.subTest(name=name + "-rescued"):
                report = inspect_stat_pips(
                    item["path"], ROOT / item["template"], item["expected_counts"])
                self.assertTrue(report["passed"])
                self.assertLessEqual(abs(report["registration"]["dy"]), 48)
        for name, item in FIXTURE["evidence"].items():
            with self.subTest(name=name):
                report = inspect_stat_pips(
                    item["path"],
                    ROOT / item["template"],
                    item["expected_counts"],
                )
                self.assertFalse(report["passed"])
                self.assertEqual(
                    tuple(report["observed_counts"].values()),
                    tuple(item["expected_counts"]),
                )
                self.assertIn(
                    item["expected_defect"],
                    {defect["code"] for defect in report["defects"]},
                )

    def test_installed_cli_writes_report_and_returns_nonzero_on_rejection(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as directory:
            card_dir = Path(directory) / "card"
            output_dir = card_dir / "outputs"
            output_dir.mkdir(parents=True)
            (card_dir / "card.json").write_text(
                json.dumps({
                    "content": {
                        "CARD_TYPE": "NOUN",
                        "RARITY_TEXT": "RARE",
                        "STAT_LORE": 3,
                        "STAT_CONTEXT": 2,
                        "STAT_COMPLEXITY": 4,
                    }
                }),
                encoding="utf-8",
            )
            candidate = output_dir / "card_1024x1536.png"

            _make_candidate(candidate)
            accepted = runner.invoke(cli, ["visual-gate", "--card-dir", str(card_dir)])
            self.assertEqual(accepted.exit_code, 0, accepted.output)
            report_path = output_dir / "visual-gate.json"
            self.assertTrue(json.loads(report_path.read_text())["passed"])

            _make_candidate(candidate, "concentric")
            rejected = runner.invoke(cli, ["visual-gate", "--card-dir", str(card_dir)])
            self.assertNotEqual(rejected.exit_code, 0)
            rejection_report = json.loads(report_path.read_text())
            self.assertFalse(rejection_report["passed"])
            self.assertIn(
                "filled-concentric-or-nonuniform",
                {item["code"] for item in rejection_report["defects"]},
            )


if __name__ == "__main__":
    unittest.main()
