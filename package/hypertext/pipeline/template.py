#!/usr/bin/env python3
"""Template refinement pipeline.

This module handles the refinement of card and lot templates using the
style reference method. It reads prompts from the template directory,
applies any revisions from revise.txt, and generates refined templates.

Templates are stored in version folders (templates/card/v001/, v002/, etc.)
with version tracking in meta.yml. This allows easy rollback to previous versions.
"""

import argparse
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml


def _log(msg: str) -> None:
    """Log a message with timestamp."""
    print(f"[template] {msg}", flush=True)


def _get_template_dir(template_type: str) -> Path:
    """Get the template directory for a given type."""
    repo_root = Path(__file__).parent.parent.parent.parent
    return repo_root / "templates" / template_type


def _get_pkg_template_path(template_type: str) -> Path:
    """Get the path to the package template (used by daily.py)."""
    repo_root = Path(__file__).parent.parent.parent.parent
    pkg_templates = repo_root / "package" / "hypertext" / "templates"

    if template_type == "card":
        return pkg_templates / "card_template.png"
    elif template_type == "lot":
        return pkg_templates / "lot_template.png"
    else:
        raise ValueError(f"Unknown template type: {template_type}")


def _get_current_version(template_dir: Path) -> int:
    """Get the current version number from meta.yml."""
    meta_path = template_dir / "meta.yml"
    if not meta_path.exists():
        return 0

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = yaml.safe_load(f) or {}

    try:
        return int(meta.get("version", 0))
    except (ValueError, TypeError):
        return 0


def _get_version_dir(template_dir: Path, version: int) -> Path:
    """Get the path to a specific version folder."""
    return template_dir / f"v{version:03d}"


def _get_subtype_dir(template_dir: Path, version: int, subtype: str = "base") -> Path:
    """Get the path to a specific subtype within a version folder."""
    return _get_version_dir(template_dir, version) / subtype


def _get_valid_subtypes(template_type: str) -> list[str]:
    """Get valid subtypes for a template type."""
    if template_type == "card":
        return ["base", "common", "uncommon", "rare", "glorious"]
    elif template_type == "lot":
        return ["base", "5-card", "6-card", "7-card"]
    return ["base"]


def _get_current_template_path(template_type: str, subtype: str = "base") -> Path:
    """Get the path to the current version's template image."""
    template_dir = _get_template_dir(template_type)
    version = _get_current_version(template_dir)
    if version == 0:
        # Fallback to legacy location
        return template_dir / "outputs" / "template_1024x1536.png"
    return _get_subtype_dir(template_dir, version, subtype) / "template_1024x1536.png"


def _get_style_refs_for_template(
    template_type: str,
    base_versions: list[int] | None = None,
) -> list[str]:
    """Get style reference images for template generation.

    For templates, we use:
    - [1] = Current template (to refine) or specified base version(s)
    - [2+] = Example cards/lots for style consistency

    Args:
        template_type: Either 'card' or 'lot'
        base_versions: Optional list of version numbers to use as base references
    """
    repo_root = Path(__file__).parent.parent.parent.parent
    template_dir = _get_template_dir(template_type)
    style_refs = []

    # Primary reference: specified versions or current template
    if base_versions:
        for v in base_versions:
            version_png = _get_version_dir(template_dir, v) / "template_1024x1536.png"
            if version_png.exists():
                style_refs.append(str(version_png))
            else:
                _log(f"WARNING: Version {v} template not found: {version_png}")
    else:
        # Default to package template (current synced version)
        pkg_template = _get_pkg_template_path(template_type)
        if pkg_template.exists():
            style_refs.append(str(pkg_template))

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


def _update_meta(meta_path: Path, new_version: int) -> None:
    """Update the meta.yml with new version and timestamp."""
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}
    else:
        meta = {}

    meta["version"] = str(new_version)
    meta["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(meta_path, "w", encoding="utf-8") as f:
        yaml.dump(meta, f, default_flow_style=False, allow_unicode=True)


def _reset_rebuild_flag(revise_path: Path) -> None:
    """Reset the Rebuild flag to false in revise.txt after a rebuild."""
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
    rebuild: bool = False,
    revision: str | None = None,
    base_versions: list[int] | None = None,
    subtype: str = "base",
    target_version: int | None = None,
) -> int:
    """Refine a template using style references.

    Args:
        template_type: Either 'card' or 'lot'
        rebuild: If True, generate fresh without using current as reference
        revision: Optional revision instructions passed via CLI
        base_versions: Optional list of version numbers to use as style references
        subtype: Template subtype (e.g., 'common', 'rare' for cards; '5-card', '7-card' for lots)
        target_version: If specified, generate into this version folder (in-place rebuild)

    Returns:
        Exit code (0 for success)
    """
    # Validate subtype
    valid_subtypes = _get_valid_subtypes(template_type)
    if subtype not in valid_subtypes:
        _log(f"ERROR: Invalid subtype '{subtype}' for {template_type}. Valid: {valid_subtypes}")
        return 1

    _log(f"Starting template refinement: {template_type}/{subtype}")

    template_dir = _get_template_dir(template_type)
    if not template_dir.exists():
        _log(f"ERROR: Template directory not found: {template_dir}")
        return 1

    revise_path = template_dir / "revise.txt"
    meta_path = template_dir / "meta.yml"

    # Check for subtype-specific prompt first, fall back to parent prompt
    subtype_prompt_path = _get_subtype_dir(template_dir, _get_current_version(template_dir) or 1, subtype) / "prompt.txt"
    if subtype_prompt_path.exists():
        prompt_path = subtype_prompt_path
    else:
        prompt_path = template_dir / "prompt.txt"

    # Determine version number
    current_version = _get_current_version(template_dir)
    if current_version == 0:
        current_version = 1  # Start at v001 if no version exists

    # If target_version specified, use it (in-place rebuild)
    if target_version is not None:
        new_version = target_version
        _log(f"Rebuilding {subtype} template in-place at v{new_version:03d}")
    else:
        # Check if this subtype already exists in current version
        current_subtype_dir = _get_subtype_dir(template_dir, current_version, subtype)
        current_subtype_png = current_subtype_dir / "template_1024x1536.png"

        if current_subtype_png.exists():
            # Subtype exists - create new version for refinement
            new_version = current_version + 1
            _log(f"Refining existing {subtype} template: v{current_version:03d} -> v{new_version:03d}")
        else:
            # Subtype doesn't exist - add it to current version
            new_version = current_version
            _log(f"Creating new {subtype} template in v{new_version:03d}")

    # Create subtype directory within version
    subtype_dir = _get_subtype_dir(template_dir, new_version, subtype)
    subtype_dir.mkdir(parents=True, exist_ok=True)
    out_png = subtype_dir / "template_1024x1536.png"

    _log(f"Output: {subtype_dir}")

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

    # Add CLI revision if provided
    if revision:
        revisions["general"] = revision
        _log(f"Using CLI revision: {revision}")

    # Build full prompt with revisions
    full_prompt = _build_refinement_prompt(base_prompt, revisions)

    # Save generated prompt (with revisions) for reference - don't overwrite source prompt
    with open(subtype_dir / "generated_prompt.txt", "w", encoding="utf-8") as f:
        f.write(full_prompt)

    # Get style references
    if base_versions:
        _log(f"Using base versions: {base_versions}")
    style_refs = _get_style_refs_for_template(template_type, base_versions)

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
        # Clean up empty subtype directory
        if subtype_dir.exists() and not out_png.exists():
            shutil.rmtree(subtype_dir)
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

    # Update meta with new version (only if version actually changed)
    if new_version > current_version:
        _update_meta(meta_path, new_version)
        _log(f"Updated meta.yml to version {new_version}")
    else:
        _log(f"Added {subtype} to existing version {new_version}")

    # Sync base subtype to package templates (daily.py uses base as default)
    if subtype == "base":
        pkg_template = _get_pkg_template_path(template_type)
        if pkg_template.parent.exists():
            shutil.copy2(out_png, pkg_template)
            _log(f"Synced to package: {pkg_template}")
        else:
            _log(f"WARNING: Package templates directory not found: {pkg_template.parent}")

    # Reset rebuild flag so user can trigger new rebuilds
    if rebuild:
        _reset_rebuild_flag(revise_path)

    _log(f"Template v{new_version:03d} complete!")
    return 0


def phase_revert(template_type: str, version: int | None = None) -> int:
    """Revert to a previous template version.

    Args:
        template_type: Either 'card' or 'lot'
        version: Version number to revert to (default: previous version)

    Returns:
        Exit code (0 for success)
    """
    template_dir = _get_template_dir(template_type)
    meta_path = template_dir / "meta.yml"

    current_version = _get_current_version(template_dir)
    if current_version == 0:
        _log("ERROR: No versions found to revert to")
        return 1

    if version is None:
        version = current_version - 1

    if version < 1:
        _log("ERROR: Cannot revert to version less than 1")
        return 1

    if version >= current_version:
        _log(f"ERROR: Version {version} is not older than current ({current_version})")
        return 1

    version_dir = _get_version_dir(template_dir, version)
    version_png = version_dir / "template_1024x1536.png"

    if not version_png.exists():
        _log(f"ERROR: Version {version} template not found: {version_png}")
        return 1

    _log(f"Reverting {template_type} template from v{current_version} to v{version}")

    # Update meta to point to old version
    _update_meta(meta_path, version)

    # Sync to package templates
    pkg_template = _get_pkg_template_path(template_type)
    if pkg_template.parent.exists():
        shutil.copy2(version_png, pkg_template)
        _log(f"Synced v{version} to package: {pkg_template}")

    _log(f"Reverted to version {version}")
    return 0


def phase_list(template_type: str) -> int:
    """List all available template versions.

    Args:
        template_type: Either 'card' or 'lot'

    Returns:
        Exit code (0 for success)
    """
    template_dir = _get_template_dir(template_type)
    current_version = _get_current_version(template_dir)

    _log(f"Template versions for {template_type}:")
    _log(f"  Current: v{current_version:03d}")
    _log("")

    # Find all version directories
    versions = []
    for item in sorted(template_dir.iterdir()):
        if item.is_dir() and item.name.startswith("v") and item.name[1:].isdigit():
            v = int(item.name[1:])
            png_exists = (item / "template_1024x1536.png").exists()
            versions.append((v, png_exists))

    if not versions:
        _log("  No version folders found")
        # Check legacy location
        legacy = template_dir / "outputs" / "template_1024x1536.png"
        if legacy.exists():
            _log(f"  Legacy template exists at: {legacy}")
        return 0

    for v, has_png in versions:
        marker = " <- current" if v == current_version else ""
        status = "✓" if has_png else "✗ (missing)"
        _log(f"  v{v:03d}: {status}{marker}")

    return 0


def phase_compile(template_type: str, version: int | None = None) -> int:
    """Compile a template version as the new v001, resetting version history.

    This takes the specified version (or current) and makes it the new v001,
    deleting all other version folders. Use this when you're happy with a
    template and want to start fresh.

    Args:
        template_type: Either 'card' or 'lot'
        version: Version to compile (default: current version)

    Returns:
        Exit code (0 for success)
    """
    template_dir = _get_template_dir(template_type)
    meta_path = template_dir / "meta.yml"

    current_version = _get_current_version(template_dir)
    if current_version == 0:
        _log("ERROR: No versions found to compile")
        return 1

    # Use specified version or current
    source_version = version if version is not None else current_version
    source_dir = _get_version_dir(template_dir, source_version)
    source_png = source_dir / "template_1024x1536.png"

    if not source_png.exists():
        _log(f"ERROR: Version {source_version} template not found: {source_png}")
        return 1

    _log(f"Compiling {template_type} template v{source_version:03d} as new v001")

    # Create temporary copy of source template
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp_path = Path(tmp.name)
    shutil.copy2(source_png, tmp_path)

    # Also save the prompt if it exists
    source_prompt = source_dir / "prompt.txt"
    tmp_prompt = None
    if source_prompt.exists():
        tmp_prompt = Path(tempfile.mktemp(suffix=".txt"))
        shutil.copy2(source_prompt, tmp_prompt)

    # Delete all version folders
    deleted = 0
    for item in sorted(template_dir.iterdir()):
        if item.is_dir() and item.name.startswith("v") and item.name[1:].isdigit():
            shutil.rmtree(item)
            deleted += 1
            _log(f"  Deleted {item.name}")

    _log(f"Deleted {deleted} version folders")

    # Create fresh v001
    new_v001 = _get_version_dir(template_dir, 1)
    new_v001.mkdir(parents=True, exist_ok=True)

    # Copy template to v001
    new_png = new_v001 / "template_1024x1536.png"
    shutil.copy2(tmp_path, new_png)
    tmp_path.unlink()  # Clean up temp file

    # Copy prompt if we saved it
    if tmp_prompt and tmp_prompt.exists():
        shutil.copy2(tmp_prompt, new_v001 / "prompt.txt")
        tmp_prompt.unlink()

    _log(f"Created new v001 from former v{source_version:03d}")

    # Update meta.yml
    _update_meta(meta_path, 1)

    # Sync to package
    pkg_template = _get_pkg_template_path(template_type)
    if pkg_template.parent.exists():
        shutil.copy2(new_png, pkg_template)
        _log(f"Synced to package: {pkg_template}")

    _log("Compile complete! Version history reset to v001")
    return 0


def phase_describe(template_type: str, version: int | None = None, subtype: str = "base") -> int:
    """Generate a rubric description for a template version.

    Uses Gemini to analyze the template image and generate a detailed
    description that can be used for grading future refinements.

    Args:
        template_type: Either 'card' or 'lot'
        version: Version to describe (default: current version)
        subtype: Template subtype (e.g., 'common', 'rare' for cards; '5-card', '7-card' for lots)

    Returns:
        Exit code (0 for success)
    """
    # Validate subtype
    valid_subtypes = _get_valid_subtypes(template_type)
    if subtype not in valid_subtypes:
        _log(f"ERROR: Invalid subtype '{subtype}' for {template_type}. Valid: {valid_subtypes}")
        return 1

    template_dir = _get_template_dir(template_type)

    current_version = _get_current_version(template_dir)
    if current_version == 0:
        _log("ERROR: No versions found to describe")
        return 1

    # Use specified version or current
    target_version = version if version is not None else current_version
    subtype_dir = _get_subtype_dir(template_dir, target_version, subtype)
    template_png = subtype_dir / "template_1024x1536.png"

    if not template_png.exists():
        _log(f"ERROR: Version {target_version}/{subtype} template not found: {template_png}")
        return 1

    _log(f"Generating rubric for {template_type} template v{target_version:03d}/{subtype}")

    # Import here to avoid circular imports
    try:
        from hypertext.gemini.review import describe_card_style_references
    except ImportError as e:
        _log(f"ERROR: Could not import gemini.review: {e}")
        return 1

    # Generate rubric using the template as a style reference
    try:
        rubric = describe_card_style_references([str(template_png)])
    except Exception as e:
        _log(f"ERROR: Failed to generate rubric: {e}")
        return 1

    # Save rubric to subtype directory
    rubric_path = subtype_dir / "rubric.txt"
    with open(rubric_path, "w", encoding="utf-8") as f:
        f.write(f"# {template_type.title()} Template v{target_version:03d}/{subtype} Rubric\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Source: {template_png.name}\n\n")
        f.write(rubric)

    _log(f"Rubric saved to: {rubric_path}")

    # Also print to console
    print("\n" + "=" * 60)
    print(f"RUBRIC FOR {template_type.upper()} TEMPLATE v{target_version:03d}/{subtype}")
    print("=" * 60)
    print(rubric)
    print("=" * 60 + "\n")

    return 0


def phase_rebuild_all(
    template_type: str,
    version: int | None = None,
    skip: list[str] | None = None,
) -> int:
    """Rebuild all subtypes in a version.

    Args:
        template_type: Either 'card' or 'lot'
        version: Version to rebuild (default: current version)
        skip: List of subtypes to skip (e.g., ['base'])

    Returns:
        Exit code (0 for success)
    """
    template_dir = _get_template_dir(template_type)
    skip = skip or []

    current_version = _get_current_version(template_dir)
    if current_version == 0:
        _log("ERROR: No versions found")
        return 1

    target_version = version if version is not None else current_version
    valid_subtypes = _get_valid_subtypes(template_type)

    _log(f"Rebuilding {template_type} template v{target_version:03d}")
    if skip:
        _log(f"Skipping: {', '.join(skip)}")

    failed = []
    succeeded = []

    for subtype in valid_subtypes:
        if subtype in skip:
            _log(f"  [{subtype}] SKIPPED")
            continue

        # Check if prompt exists for this subtype
        subtype_dir = _get_subtype_dir(template_dir, target_version, subtype)
        prompt_file = subtype_dir / "prompt.txt"

        if not prompt_file.exists():
            # Check parent prompt
            parent_prompt = template_dir / "prompt.txt"
            if not parent_prompt.exists():
                _log(f"  [{subtype}] SKIPPED (no prompt)")
                continue

        _log(f"  [{subtype}] Generating...")

        # Call phase_refine for this subtype with target_version for in-place rebuild
        result = phase_refine(
            template_type=template_type,
            rebuild=True,
            subtype=subtype,
            target_version=target_version,
        )

        if result == 0:
            succeeded.append(subtype)
            _log(f"  [{subtype}] SUCCESS")
        else:
            failed.append(subtype)
            _log(f"  [{subtype}] FAILED")

    _log("")
    _log(f"Rebuild complete: {len(succeeded)} succeeded, {len(failed)} failed")
    if failed:
        _log(f"Failed subtypes: {', '.join(failed)}")
        return 1

    return 0


def main() -> int:
    """CLI entrypoint for template refinement pipeline."""
    parser = argparse.ArgumentParser(description="Template Refinement Pipeline")
    parser.add_argument(
        "--type",
        required=True,
        choices=["card", "lot"],
        help="Template type to manage"
    )
    parser.add_argument(
        "--phase",
        required=True,
        choices=["refine", "revert", "list", "compile", "describe", "rebuild"],
        help="Pipeline phase to run"
    )
    parser.add_argument(
        "--from-scratch",
        action="store_true",
        dest="rebuild_flag",
        help="Rebuild from scratch (ignore current template as reference)"
    )
    parser.add_argument(
        "--version",
        type=int,
        help="Version number (for revert or compile)"
    )
    parser.add_argument(
        "--revision",
        type=str,
        help="Revision instructions (overrides general_revision in revise.txt)"
    )
    parser.add_argument(
        "--base-version",
        type=int,
        action="append",
        dest="base_versions",
        help="Use specific version(s) as style reference (can specify multiple)"
    )
    parser.add_argument(
        "--subtype",
        type=str,
        default="base",
        help="Template subtype (card: base/common/uncommon/rare/glorious; lot: base/5-card/6-card/7-card)"
    )
    parser.add_argument(
        "--skip",
        type=str,
        action="append",
        help="Subtypes to skip during rebuild (can specify multiple, e.g., --skip base --skip common)"
    )

    args = parser.parse_args()

    if args.phase == "refine":
        return phase_refine(
            template_type=args.type,
            rebuild=args.rebuild_flag,
            revision=args.revision,
            base_versions=args.base_versions,
            subtype=args.subtype,
        )
    elif args.phase == "revert":
        return phase_revert(
            template_type=args.type,
            version=args.version,
        )
    elif args.phase == "list":
        return phase_list(template_type=args.type)
    elif args.phase == "compile":
        return phase_compile(
            template_type=args.type,
            version=args.version,
        )
    elif args.phase == "describe":
        return phase_describe(
            template_type=args.type,
            version=args.version,
            subtype=args.subtype,
        )
    elif args.phase == "rebuild":
        return phase_rebuild_all(
            template_type=args.type,
            version=args.version,
            skip=args.skip,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
