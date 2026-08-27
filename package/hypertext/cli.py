#!/usr/bin/env python3
"""Hypertext CLI - Biblical word-study trading card game toolkit."""

import json
import sys
from contextlib import contextmanager

import click


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Hypertext - Biblical word-study trading card game toolkit.

    Generate cards, build galleries, manage watermarks, and more.
    """
    pass


@cli.command()
@click.option("--series", required=True, help="Path to series directory")
@click.option("--phase", type=click.Choice(["plan", "imagegen", "full"]), required=True)
@click.option("--batch", type=int, default=1, help="Number of cards to generate")
@click.option("--parallel", type=int, default=1, help="Parallel workers for image generation")
@click.option("--auto", is_flag=True, help="Use the production planner")
@click.option("--skip-polish", is_flag=True, help="Skip polish step")
@click.option("--skip-watermark", is_flag=True, help="Skip watermark step")
def generate(series, phase, batch, parallel, auto, skip_polish, skip_watermark):
    """Run the supported daily package pipeline."""
    arguments = ["--phase", phase, "--series", series, "--batch", str(batch),
                 "--parallel", str(parallel)]
    if auto:
        arguments.append("--auto")
    if skip_polish:
        arguments.append("--skip-polish")
    if skip_watermark:
        arguments.append("--skip-watermark")
    _run_daily(arguments)


@contextmanager
def _daily_argv(arguments):
    previous = sys.argv
    sys.argv = ["hypertext.pipeline.daily", *arguments]
    try:
        yield
    finally:
        sys.argv = previous


def _run_daily(arguments):
    from hypertext.pipeline.daily import main

    with _daily_argv(arguments):
        result = main()
    if result:
        raise click.ClickException(f"daily pipeline exited with status {result}")


def _unsupported(command):
    raise click.ClickException(
        f"'{command}' is not supported by the installed CLI; use the documented package module entry point"
    )


@cli.command()
@click.option("--series", default="demo_cards", help="Demo cards directory")
@click.option("--batch", type=int, default=1, help="Number of demo cards to generate")
@click.option("--parallel", type=int, default=1, help="Parallel workers")
@click.option("--skip-polish", is_flag=True, help="Skip polish step")
def demo(series, batch, parallel, skip_polish):
    """Generate demo cards."""
    _unsupported("demo")


@cli.command()
@click.option("--card-dir", required=True, help="Path to card directory")
@click.option("--threshold", type=float, default=0.7, help="Quality threshold")
@click.option("--describe-only", is_flag=True, help="Only describe, don't score")
def review(card_dir, threshold, describe_only):
    """Review a card for quality."""
    _unsupported("review")


@cli.command("visual-gate")
@click.option(
    "--card-dir",
    required=True,
    type=click.Path(path_type=str),
    help="Card directory containing card.json and outputs/card_1024x1536.png",
)
@click.option(
    "--candidate",
    type=click.Path(path_type=str),
    help="Candidate PNG override (defaults to the card output)",
)
@click.option(
    "--report",
    "report_path",
    type=click.Path(path_type=str),
    help="JSON report path (defaults to card-dir/outputs/visual-gate.json)",
)
def visual_gate(card_dir, candidate, report_path):
    """Reject stat pips that differ from the exact canonical template family."""
    from pathlib import Path

    from hypertext.cards.stat_pip_gate import (
        StatPipGateError,
        defect_summary,
        inspect_card_stat_pips,
    )

    directory = Path(card_dir)
    destination = Path(report_path) if report_path else directory / "outputs" / "visual-gate.json"
    try:
        result = inspect_card_stat_pips(
            directory,
            candidate_path=Path(candidate) if candidate else None,
            report_path=destination,
        )
    except StatPipGateError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(json.dumps({
        "contract": result["contract"],
        "passed": result["passed"],
        "report": str(destination),
        "defects": result["defects"],
    }, sort_keys=True))
    if not result["passed"]:
        raise click.ClickException("stat pip visual gate rejected candidate: " + defect_summary(result))


@cli.command()
@click.option("--series", required=True, help="Path to series directory")
@click.option("--out-dir", default="_site", help="Output directory")
def gallery(series, out_dir):
    """Build static gallery site."""
    _unsupported("gallery")


@cli.group()
def watermark():
    """Watermark management commands."""
    pass


@watermark.command("apply")
@click.option("--card-dir", required=True, help="Path to card directory")
@click.option("--in", "in_path", help="Input PNG path (default: card_dir/outputs/card_1024x1536.png)")
@click.option("--out", "out_path", help="Output PNG path (default: same as input)")
def watermark_apply(card_dir, in_path, out_path):
    """Apply watermark to a card."""
    _unsupported("watermark apply")


@watermark.command("verify")
@click.option("--card-dir", required=True, help="Path to card directory")
@click.option("--svg", help="Path to watermark SVG (default: card_dir/watermark.svg)")
def watermark_verify(card_dir, svg):
    """Verify watermark authenticity."""
    _unsupported("watermark verify")


@cli.group()
def convert():
    """Image conversion utilities."""
    pass


@convert.command("jpeg-to-png")
@click.argument("path", type=click.Path(exists=True))
@click.option("--keep", is_flag=True, help="Keep original JPEG files")
def convert_jpeg_to_png(path, keep):
    """Convert JPEG images to PNG format."""
    from hypertext.utils.image import convert_jpeg_to_png as do_convert
    do_convert(path, keep_original=keep)


@cli.command()
@click.option("--series", required=True, help="Path to series directory")
@click.option("--phase", type=click.Choice(["init", "generate", "render", "batch", "export"]), required=True)
@click.option("--parallel", type=int, default=1, help="Parallel workers")
@click.option("--target", type=click.Choice(["playingcards", "makeplayingcards", "thegamecrafter"]),
              help="Export target (required for export phase)")
def lot(series, phase, parallel, target):
    """Manage LOT (phase) cards."""
    _unsupported("lot")


if __name__ == "__main__":
    cli()
