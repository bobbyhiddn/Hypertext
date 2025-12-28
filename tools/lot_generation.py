#!/usr/bin/env python3
"""
Lot (Phase Card) Generation Pipeline for Hypertext.

Phase names and compositions are universal (loaded from templates/phases.yml).
Only flavor text and context vary per series (stored in series/X/lots/lot_content.yml).

Phases:
  - init: Create lot_content.yml template for a series
  - generate: Generate context/flavor via Gemini for series theme
  - render: Render all 30 phase card PNGs
  - batch: Full pipeline (generate + render)
  - export: Package for playtest platforms

Usage:
  python lot_generation.py --phase init --series series/2026-Q1
  python lot_generation.py --phase generate --series series/2026-Q1
  python lot_generation.py --phase render --series series/2026-Q1
  python lot_generation.py --phase batch --series series/2026-Q1
  python lot_generation.py --phase export --series series/2026-Q1 --target playingcards
"""

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_DIR.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
UNIVERSAL_PHASES_PATH = TEMPLATES_DIR / "phases.yml"


def _log(msg: str) -> None:
    """Log a message to stderr."""
    print(msg, file=sys.stderr)


def load_universal_phases() -> list[dict[str, Any]]:
    """Load universal phase definitions from templates/phases.yml."""
    if yaml is None:
        raise RuntimeError("pyyaml required: pip install pyyaml")
    if not UNIVERSAL_PHASES_PATH.exists():
        raise RuntimeError(f"Universal phases file not found: {UNIVERSAL_PHASES_PATH}")
    with open(UNIVERSAL_PHASES_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("phases", [])


def load_series_content(series_dir: Path) -> dict[int, dict[str, str]]:
    """Load series-specific flavor/context from lot_content.yml."""
    if yaml is None:
        raise RuntimeError("pyyaml required: pip install pyyaml")
    content_path = series_dir / "lots" / "lot_content.yml"
    if not content_path.exists():
        return {}
    with open(content_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("content", {})


def get_series_theme(series_dir: Path) -> str:
    """Get theme from series stats.yml."""
    if yaml is None:
        raise RuntimeError("pyyaml required: pip install pyyaml")
    stats_path = series_dir / "stats.yml"
    if not stats_path.exists():
        return ""
    with open(stats_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("theme", "")


def phase_init(series_dir: Path) -> int:
    """Create lot_content.yml template with empty flavor/context for all 30 phases."""
    if yaml is None:
        _log("Error: pyyaml required. Install with: pip install pyyaml")
        return 1

    lots_dir = series_dir / "lots"
    lots_dir.mkdir(parents=True, exist_ok=True)

    content_path = lots_dir / "lot_content.yml"
    if content_path.exists():
        _log(f"{content_path} already exists. Delete to regenerate.")
        return 1

    phases = load_universal_phases()
    theme = get_series_theme(series_dir)

    content: dict[str, Any] = {
        "series": series_dir.name,
        "theme": theme,
        "content": {}
    }

    for phase in phases:
        content["content"][phase["id"]] = {
            "flavor": "",
            "context": ""
        }

    with open(content_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(content, f, sort_keys=False, allow_unicode=True, default_flow_style=False)

    _log(f"Created {content_path} with {len(phases)} empty entries.")
    return 0


def phase_generate(series_dir: Path) -> int:
    """Use Gemini to generate flavor text and context for each phase."""
    if yaml is None:
        _log("Error: pyyaml required. Install with: pip install pyyaml")
        return 1

    # Import gemini_text from the same tools directory
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        from gemini_text import generate_text
    except ImportError as e:
        _log(f"Error importing gemini_text: {e}")
        return 1

    phases = load_universal_phases()
    theme = get_series_theme(series_dir)
    content_path = series_dir / "lots" / "lot_content.yml"

    if not content_path.exists():
        _log(f"Run --phase init first to create {content_path}")
        return 1

    with open(content_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    existing_content = data.get("content", {})

    for phase in phases:
        pid = phase["id"]
        name = phase["name"]

        # Skip if already has content
        entry = existing_content.get(pid, {})
        if entry.get("flavor") and entry.get("context"):
            _log(f"[{pid:02d}] {name}: already has content, skipping")
            continue

        _log(f"[{pid:02d}] {name}: generating...")

        # Generate flavor
        flavor_prompt = f"""Generate a short, evocative flavor subtitle for a Biblical trading card game phase card.

Phase name: {name}
Card requirement: {phase['display']}
Series theme: {theme}

The flavor should:
- Be 5-12 words
- Sound poetic/biblical
- Connect to the phase name's meaning
- NOT explain the game mechanic

Return only the flavor text, no quotes or explanation."""

        try:
            flavor = generate_text(flavor_prompt, temperature=0.7).strip().strip('"')
        except Exception as e:
            _log(f"    Error generating flavor: {e}")
            flavor = ""

        # Generate context
        context_prompt = f"""Generate an educational context paragraph for a Biblical trading card game phase card.

Phase name: {name}
Series theme: {theme}

The context should:
- Be 2-4 sentences
- Explain the Biblical/theological significance of the term "{name}"
- Reference specific scripture where relevant
- Be educational, not gameplay-related
- Match the tone of seminary-level Bible study

Return only the paragraph, no quotes or explanation."""

        try:
            context = generate_text(context_prompt, temperature=0.5).strip().strip('"')
        except Exception as e:
            _log(f"    Error generating context: {e}")
            context = ""

        existing_content[pid] = {
            "flavor": flavor,
            "context": context
        }

        if flavor:
            _log(f"    flavor: {flavor[:50]}...")

    # Save updated content
    data["content"] = existing_content
    with open(content_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=80, default_flow_style=False)

    _log(f"Updated {content_path}")
    return 0


def phase_render(series_dir: Path, parallel: int = 1) -> int:
    """Render all 30 phase card PNGs using Gemini with style references."""
    if yaml is None:
        _log("Error: pyyaml required. Install with: pip install pyyaml")
        return 1

    # Import lot_renderer from the same tools directory
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        from lot_renderer import render_lot_card_with_series
    except ImportError as e:
        _log(f"Error importing lot_renderer: {e}")
        _log("Make sure lot_renderer.py exists in the tools directory.")
        return 1

    phases = load_universal_phases()
    content = load_series_content(series_dir)
    theme = get_series_theme(series_dir)
    lots_dir = series_dir / "lots"

    rendered_count = 0
    error_count = 0

    for phase in phases:
        pid = phase["id"]
        name = phase["name"]
        slug = name.lower().replace(" ", "-")

        card_dir = lots_dir / f"{pid:02d}-{slug}"
        card_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir = card_dir / "outputs"
        outputs_dir.mkdir(exist_ok=True)

        phase_content = content.get(pid, {})

        card_data = {
            **phase,
            "flavor": phase_content.get("flavor", ""),
            "context": phase_content.get("context", ""),
            "series": series_dir.name,
            "theme": theme,
        }

        out_path = outputs_dir / "lot_1024x1536.png"

        _log(f"[{pid:02d}] Rendering {name}...")

        try:
            render_lot_card_with_series(card_data, out_path, series_dir)
            rendered_count += 1
        except Exception as e:
            _log(f"    Error rendering: {e}")
            error_count += 1
            continue

        # Write meta.yml
        meta = {
            "id": pid,
            "name": name,
            "cards": phase["cards"],
            "points": phase["points"],
            "display": phase["display"],
            "flavor": card_data["flavor"],
            "context": card_data["context"],
        }
        with open(card_dir / "meta.yml", "w", encoding="utf-8") as f:
            yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True, default_flow_style=False)

    _log(f"Rendered {rendered_count} lot cards to {lots_dir}")
    if error_count:
        _log(f"  ({error_count} errors)")
    return 0 if error_count == 0 else 1


def phase_batch(series_dir: Path) -> int:
    """Full pipeline: init (if needed) + generate + render."""
    content_path = series_dir / "lots" / "lot_content.yml"

    if not content_path.exists():
        rc = phase_init(series_dir)
        if rc != 0:
            return rc

    rc = phase_generate(series_dir)
    if rc != 0:
        return rc

    return phase_render(series_dir)


def phase_export(series_dir: Path, target: str) -> int:
    """Package lots for target platform."""
    # Import lot_exporter from the same tools directory
    sys.path.insert(0, str(TOOLS_DIR))
    try:
        from lot_exporter import export_for_platform
    except ImportError as e:
        _log(f"Error importing lot_exporter: {e}")
        _log("Make sure lot_exporter.py exists in the tools directory.")
        return 1

    return export_for_platform(series_dir, target)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lot (Phase Card) Generation Pipeline for Hypertext",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python lot_generation.py --phase init --series series/2026-Q1
  python lot_generation.py --phase generate --series series/2026-Q1
  python lot_generation.py --phase render --series series/2026-Q1
  python lot_generation.py --phase batch --series series/2026-Q1
  python lot_generation.py --phase export --series series/2026-Q1 --target playingcards
"""
    )
    parser.add_argument(
        "--phase",
        required=True,
        choices=["init", "generate", "render", "batch", "export"],
        help="Pipeline phase to run"
    )
    parser.add_argument(
        "--series",
        required=True,
        help="Path to series directory (e.g., series/2026-Q1)"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Number of cards to render in parallel (default: 1)"
    )
    parser.add_argument(
        "--target",
        choices=["playingcards", "makeplayingcards", "thegamecrafter"],
        help="Export target platform (required for export phase)"
    )
    args = parser.parse_args()

    series_dir = Path(args.series)
    if not series_dir.exists():
        _log(f"Error: Series directory does not exist: {series_dir}")
        return 1

    if args.phase == "init":
        return phase_init(series_dir)
    elif args.phase == "generate":
        return phase_generate(series_dir)
    elif args.phase == "render":
        return phase_render(series_dir, args.parallel)
    elif args.phase == "batch":
        return phase_batch(series_dir)
    elif args.phase == "export":
        if not args.target:
            _log("Error: --target required for export phase")
            return 2
        return phase_export(series_dir, args.target)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
