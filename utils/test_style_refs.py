#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path


def _find_latest_card_images(*, cards_root: Path, out_name: str, limit: int) -> list[Path]:
    matches: list[Path] = []
    if not cards_root.exists():
        return []

    for p in cards_root.rglob(out_name):
        if p.is_file() and p.parent.name == "outputs":
            matches.append(p)

    matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test Gemini style references using template + recent rendered cards"
    )
    parser.add_argument("--prompt", help="Prompt text")
    parser.add_argument("--prompt-file", help="Path to prompt text file")
    parser.add_argument("--out", required=True, help="Output PNG path")

    parser.add_argument(
        "--template",
        default=str(Path("tools") / "clean_template_final.png"),
        help="Template/reference image path (first style ref)",
    )
    parser.add_argument(
        "--cards-root",
        default=str(Path("series")),
        help="Root folder to search for rendered card images (default: series)",
    )
    parser.add_argument(
        "--n-cards",
        type=int,
        default=2,
        help="How many recent rendered cards to include as additional style refs",
    )
    parser.add_argument(
        "--style",
        action="append",
        default=[],
        help="Additional style ref image path (repeatable; appended after template + recent cards)",
    )

    parser.add_argument(
        "--model",
        default="gemini-3-pro-image-preview",
        help="Gemini model ID (passed through to gemini_style.py)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved style refs and command without calling Gemini",
    )

    args = parser.parse_args()

    prompt_text = args.prompt
    if args.prompt_file:
        if not os.path.exists(args.prompt_file):
            print(f"Error: Prompt file not found: {args.prompt_file}", file=sys.stderr)
            return 1
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompt_text = f.read().strip()

    if not prompt_text:
        print("Error: Must provide either --prompt or --prompt-file", file=sys.stderr)
        return 1

    template_path = Path(args.template)
    if not template_path.exists():
        print(f"Error: Template image not found: {template_path}", file=sys.stderr)
        return 1

    cards_root = Path(args.cards_root)
    recent = _find_latest_card_images(
        cards_root=cards_root,
        out_name="card_1024x1536.png",
        limit=max(0, int(args.n_cards)),
    )

    style_refs: list[Path] = [template_path]
    style_refs.extend(recent)
    style_refs.extend(Path(p) for p in (args.style or []))

    if len(style_refs) > 16:
        print(
            f"Error: Too many style refs ({len(style_refs)}). Maximum supported is 16.",
            file=sys.stderr,
        )
        return 1

    if args.dry_run:
        print("Resolved style references:")
        for i, p in enumerate(style_refs, start=1):
            print(f"[{i}] {p}")

    gemini_style_py = Path(__file__).with_name("gemini_style.py")
    if not gemini_style_py.exists():
        print(f"Error: gemini_style.py not found next to this script: {gemini_style_py}", file=sys.stderr)
        return 1

    cmd: list[str] = [
        sys.executable,
        str(gemini_style_py),
        "--out",
        str(args.out),
        "--model",
        str(args.model),
    ]

    if args.prompt_file:
        cmd += ["--prompt-file", str(args.prompt_file)]
    else:
        cmd += ["--prompt", str(prompt_text)]

    for p in style_refs:
        cmd += ["--style", str(p)]

    if args.dry_run:
        print("\nCommand:")
        print(" ".join(cmd))
        return 0

    subprocess.check_call(cmd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
