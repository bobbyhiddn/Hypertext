"""Archive-aware resolution for historically recorded repository paths."""
from __future__ import annotations
from pathlib import Path

ARCHIVE_ROOTS = (
    Path("templates/archive/pre-v002-lot-rework"),
    Path("templates/archive/matrix-provenance"),
)


def resolve_recorded(root: Path, relative: str | Path) -> Path:
    """Resolve a manifest-recorded repo-relative path, falling back to the archives.

    Provenance manifests record paths as they were at generation time; retired
    assets move under templates/archive/ with their internal structure intact,
    so recorded paths and digests keep verifying after the move.
    """
    relative = Path(relative)
    if relative.is_absolute():
        return relative
    primary = root / relative
    if primary.exists():
        return primary
    for archive in ARCHIVE_ROOTS:
        candidate = root / archive / relative
        if candidate.exists():
            return candidate
    return primary
