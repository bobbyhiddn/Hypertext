import json
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner
from jsonschema import Draft7Validator

from hypertext.cli import cli
from hypertext.pipeline import daily


ROOT = Path(__file__).resolve().parents[2]


def test_installed_generate_delegates_to_daily_pipeline(monkeypatch):
    observed = []

    def fake_main():
        observed.append(sys.argv.copy())
        return 0

    monkeypatch.setattr(daily, "main", fake_main)
    result = CliRunner().invoke(
        cli,
        ["generate", "--series", "series/test", "--phase", "plan", "--auto", "--batch", "2"],
    )

    assert result.exit_code == 0, result.output
    assert observed == [[
        "hypertext.pipeline.daily", "--phase", "plan", "--series", "series/test",
        "--batch", "2", "--parallel", "1", "--auto",
    ]]


@pytest.mark.parametrize(
    "arguments,name",
    [
        (["demo"], "demo"),
        (["review", "--card-dir", "card"], "review"),
        (["gallery", "--series", "series"], "gallery"),
        (["watermark", "apply", "--card-dir", "card"], "watermark apply"),
        (["watermark", "verify", "--card-dir", "card"], "watermark verify"),
        (["lot", "--series", "series", "--phase", "init"], "lot"),
    ],
)
def test_legacy_click_surfaces_fail_closed(arguments, name):
    result = CliRunner().invoke(cli, arguments)

    assert result.exit_code != 0
    assert f"'{name}' is not supported" in result.output
    assert "Generating" not in result.output
    assert "Building" not in result.output


def test_imagegen_rejects_card_dir_instead_of_ignoring_it(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["hypertext.pipeline.daily", "--phase", "imagegen", "--series", "series/test",
         "--card-dir", "cards/selected"],
    )

    with pytest.raises(SystemExit) as exc:
        daily.main()

    assert exc.value.code == 2
    assert "--card-dir is not supported with --phase imagegen" in capsys.readouterr().err


def test_prompt_template_uses_schema_canonical_game_name():
    template = json.loads((ROOT / "templates/card_prompt_template.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schema/hypertext_card.schema.json").read_text(encoding="utf-8"))
    game_name_schema = schema["properties"]["style_guide"]["properties"]["game_name"]

    assert game_name_schema == {"type": "string", "const": "Hypertext"}
    assert template["style_guide"]["game_name"] == "Hypertext"
    Draft7Validator(game_name_schema).validate(template["style_guide"]["game_name"])


def test_documentation_names_current_entry_points_phases_flags_and_gate():
    root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
    package_readme = (ROOT / "package/README.md").read_text(encoding="utf-8")

    assert "tools/daily_pipeline.py" not in root_readme
    assert "python -m hypertext.pipeline.daily" in root_readme
    pipeline_docs = package_readme.split("### Pipeline", 1)[1].split("### Template Refinement", 1)[0]
    assert "--cards-dir" not in pipeline_docs
    assert "--phase art" not in pipeline_docs
    assert "--phase composite" not in pipeline_docs
    assert "--phase imagegen" in pipeline_docs
    assert "every dimension must reach 100" in pipeline_docs


def test_documentation_distinguishes_review_gate_from_daily_grade_gate():
    package_readme = (ROOT / "package/README.md").read_text(encoding="utf-8")
    review_source = (ROOT / "package/hypertext/gemini/review.py").read_text(encoding="utf-8")
    pipeline_docs = package_readme.split("### Pipeline", 1)[1].split("### Template Refinement", 1)[0]
    gemini_docs = package_readme.split("### Gemini Integration", 1)[1].split("## Quality Grading", 1)[0]
    quality_docs = package_readme.split("## Quality Grading", 1)[1]

    assert 'parser.add_argument("--threshold", type=int, default=90' in review_source
    assert "python -m hypertext.gemini.review --card-dir path/to/card --threshold 90" in gemini_docs
    assert "--threshold 85" not in gemini_docs
    assert "**Pass threshold:** 90 points with 0 style mismatches" in quality_docs
    assert "every dimension must reach 100" in pipeline_docs
