#!/usr/bin/env python3
"""Template refinement pipeline.

This module handles the refinement of card and lot templates using the
style reference method. It reads prompts from the template directory,
applies any revisions from revise.txt, and generates refined templates.
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml


def _log(msg: str) -> None:
    """Log a message with timestamp."""
    print(f"[template] {msg}", flush=True)


def _get_template_dir(template_type: str, version: str) -> Path:
    """Get the template directory for a given type and version."""
    repo_root = Path(__file__).parent.parent.parent.parent
    return repo_root / "templates" / template_type / f"v{version}"


def _get_current_template_path(template_type: str) -> Path:
    """Get the path to the current production template."""
    repo_root = Path(__file__).parent.parent.parent.parent
    pkg_templates = repo_root / "package" / "hypertext" / "templates"

    if template_type == "card":
        return pkg_templates / "card_template.png"
    elif template_type == "lot":
        return pkg_templates / "lot_template.png"
    else:
        raise ValueError(f"Unknown template type: {template_type}")


def _get_style_refs_for_template(template_type: str) -> list[str]:
    """Get style reference images for template generation.

    For templates, we use:
    - [1] = Current template (to refine)
    - [2+] = Example cards/lots for style consistency
    """
    repo_root = Path(__file__).parent.parent.parent.parent
    style_refs = []

    # Primary reference: current template
    current = _get_current_template_path(template_type)
    if current.exists():
        style_refs.append(str(current))

    # Add example references based on type
    if template_type == "card":
        # Use existing example cards from templates directory
        pkg_templates = repo_root / "package" / "hypertext" / "templates"
        for name in ["Creation.png", "Epistle.png"]:
            ref = pkg_templates / name
            if ref.exists():
                style_refs.append(str(ref))

        # Also check series for good examples
        series_cards = repo_root / "series" / "2026-Q1" / "cards"
        if series_cards.exists():
            for card_dir in sorted(series_cards.iterdir())[:2]:
                card_png = card_dir / "outputs" / "card_1024x1536.png"
                if card_png.exists():
                    style_refs.append(str(card_png))

    elif template_type == "lot":
        # Use lot examples from templates/lots
        lot_templates = repo_root / "templates" / "lots"
        for name in ["Creation.png", "Epistle.png", "Lot_Template.png"]:
            ref = lot_templates / name
            if ref.exists():
                style_refs.append(str(ref))

        # Also check series lots
        series_lots = repo_root / "series" / "2026-Q1" / "lots"
        if series_lots.exists():
            for lot_dir in sorted(series_lots.iterdir())[:2]:
                lot_png = lot_dir / "outputs" / "lot_1024x1536.png"
                if lot_png.exists():
                    style_refs.append(str(lot_png))

    # Limit to reasonable number
    return style_refs[:5]


def _parse_revise_form(revise_path: Path) -> dict:
    """Parse the revise.txt form to extract revision requests."""
    revisions = {
        "rebuild": False,
        "frame": "",
        "layout": "",
        "typography": "",
        "color": "",
        "stats": "",
        "icon": "",
        "banner": "",
        "general": "",
    }

    if not revise_path.exists():
        return revisions

    with open(revise_path, "r", encoding="utf-8") as f:
        content = f.read()

    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("#") or not line:
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()

            # Skip placeholder values
            if value.startswith("<") and value.endswith(">"):
                continue

            if key == "rebuild":
                revisions["rebuild"] = value.lower() == "true"
            elif key == "frame_revision":
                revisions["frame"] = value
            elif key == "layout_revision":
                revisions["layout"] = value
            elif key == "typography_revision":
                revisions["typography"] = value
            elif key == "color_revision":
                revisions["color"] = value
            elif key == "stats_revision":
                revisions["stats"] = value
            elif key == "icon_revision":
                revisions["icon"] = value
            elif key == "banner_revision":
                revisions["banner"] = value
            elif key == "general_revision":
                revisions["general"] = value

    return revisions


def _build_refinement_prompt(base_prompt: str, revisions: dict) -> str:
    """Build the full prompt by appending revision instructions."""
    prompt_parts = [base_prompt.strip()]

    revision_sections = []

    if revisions.get("frame"):
        revision_sections.append(f"FRAME CHANGES: {revisions['frame']}")
    if revisions.get("layout"):
        revision_sections.append(f"LAYOUT CHANGES: {revisions['layout']}")
    if revisions.get("typography"):
        revision_sections.append(f"TYPOGRAPHY CHANGES: {revisions['typography']}")
    if revisions.get("color"):
        revision_sections.append(f"COLOR CHANGES: {revisions['color']}")
    if revisions.get("stats"):
        revision_sections.append(f"STATS CHANGES: {revisions['stats']}")
    if revisions.get("icon"):
        revision_sections.append(f"ICON CHANGES: {revisions['icon']}")
    if revisions.get("banner"):
        revision_sections.append(f"BANNER CHANGES: {revisions['banner']}")
    if revisions.get("general"):
        revision_sections.append(f"ADDITIONAL CHANGES: {revisions['general']}")

    if revision_sections:
        prompt_parts.append("\n\nREQUESTED REFINEMENTS:")
        prompt_parts.extend(revision_sections)

    return "\n".join(prompt_parts)


def _update_meta(meta_path: Path, version: str) -> None:
    """Update the meta.yml with generation timestamp."""
    if not meta_path.exists():
        return

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = yaml.safe_load(f) or {}

    meta["updated"] = datetime.now().strftime("%Y-%m-%d")
    meta["version"] = version

    with open(meta_path, "w", encoding="utf-8") as f:
        yaml.dump(meta, f, default_flow_style=False, allow_unicode=True)


def _reset_rebuild_flag(revise_path: Path) -> None:
    """Reset the Rebuild flag to false in revise.txt after a rebuild.

    This allows the user to trigger new rebuilds by setting it to true again.
    """
    if not revise_path.exists():
        return

    with open(revise_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace "Rebuild: true" with "Rebuild: false" (case-insensitive for value)
    new_content = re.sub(
        r'^(Rebuild:\s*)true\s*$',
        r'\1false',
        content,
        flags=re.MULTILINE | re.IGNORECASE
    )

    if new_content != content:
        with open(revise_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        _log("Reset Rebuild flag to false in revise.txt")


def phase_refine(
    template_type: str,
    version: str,
    rebuild: bool = False,
) -> int:
    """Refine a template using style references.

    Args:
        template_type: Either 'card' or 'lot'
        version: Version number (e.g., '1', '2')
        rebuild: If True, generate fresh without using current as reference

    Returns:
        Exit code (0 for success)
    """
    _log(f"Starting template refinement: {template_type} v{version}")

    template_dir = _get_template_dir(template_type, version)
    if not template_dir.exists():
        _log(f"ERROR: Template directory not found: {template_dir}")
        return 1

    prompt_path = template_dir / "prompt.txt"
    revise_path = template_dir / "revise.txt"
    meta_path = template_dir / "meta.yml"
    outputs_dir = template_dir / "outputs"
    out_png = outputs_dir / "template_1024x1536.png"

    # Ensure outputs directory exists
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # Read base prompt
    if not prompt_path.exists():
        _log(f"ERROR: Prompt file not found: {prompt_path}")
        return 1

    with open(prompt_path, "r", encoding="utf-8") as f:
        base_prompt = f.read().strip()

    # Parse revisions
    revisions = _parse_revise_form(revise_path)
    if revisions["rebuild"]:
        rebuild = True
        _log("Rebuild requested via revise.txt")

    # Build full prompt with revisions
    full_prompt = _build_refinement_prompt(base_prompt, revisions)

    # Get style references
    style_refs = _get_style_refs_for_template(template_type)

    if not style_refs:
        _log("WARNING: No style references found, using basic image generation")
        # Fall back to basic generation
        cmd = [
            sys.executable, "-m", "hypertext.gemini.image",
            "--prompt", full_prompt,
            "--out", str(out_png)
        ]
    else:
        _log(f"Using {len(style_refs)} style references:")
        for ref in style_refs:
            _log(f"  - {ref}")

        # Write prompt to temp file for style generation
        temp_prompt = template_dir / ".temp_prompt.txt"
        with open(temp_prompt, "w", encoding="utf-8") as f:
            f.write(full_prompt)

        cmd = [
            sys.executable, "-m", "hypertext.gemini.style",
            "--prompt-file", str(temp_prompt),
        ]

        for ref in style_refs:
            cmd.extend(["--style", ref])

        cmd.extend(["--out", str(out_png)])

    _log(f"Running: {' '.join(cmd)}")

    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        _log(f"ERROR: Image generation failed: {e}")
        return 1
    finally:
        # Clean up temp file
        temp_prompt = template_dir / ".temp_prompt.txt"
        if temp_prompt.exists():
            temp_prompt.unlink()

    if not out_png.exists():
        _log(f"ERROR: Output not created: {out_png}")
        return 1

    _log(f"Template generated: {out_png}")

    # Update meta
    _update_meta(meta_path, version)

    # Reset rebuild flag so user can trigger new rebuilds
    if rebuild:
        _reset_rebuild_flag(revise_path)

    return 0


def main() -> int:
    """CLI entrypoint for template refinement pipeline."""
    parser = argparse.ArgumentParser(description="Template Refinement Pipeline")
    parser.add_argument(
        "--type",
        required=True,
        choices=["card", "lot"],
        help="Template type to refine"
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Version number (e.g., '1', '2')"
    )
    parser.add_argument(
        "--phase",
        required=True,
        choices=["refine"],
        help="Pipeline phase to run"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild from scratch (ignore current template as reference)"
    )

    args = parser.parse_args()

    if args.phase == "refine":
        return phase_refine(
            template_type=args.type,
            version=args.version,
            rebuild=args.rebuild,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
