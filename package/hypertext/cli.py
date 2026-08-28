#!/usr/bin/env python3
"""Hypertext CLI - Biblical word-study trading card game toolkit."""

import json

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
@click.option("--phase", type=click.Choice(["plan", "image", "batch", "full"]), required=True)
@click.option("--batch", type=int, default=1, help="Number of cards to generate")
@click.option("--parallel", type=int, default=1, help="Parallel workers for image generation")
@click.option("--skip-polish", is_flag=True, help="Skip polish step")
@click.option("--skip-watermark", is_flag=True, help="Skip watermark step")
def generate(series, phase, batch, parallel, skip_polish, skip_watermark):
    """Generate cards for a series."""
    click.echo(f"Generating cards: series={series}, phase={phase}, batch={batch}")
    # TODO: Wire up to pipeline logic
    raise NotImplementedError("generate command not yet implemented")


@cli.command()
@click.option("--series", default="demo_cards", help="Demo cards directory")
@click.option("--batch", type=int, default=1, help="Number of demo cards to generate")
@click.option("--parallel", type=int, default=1, help="Parallel workers")
@click.option("--skip-polish", is_flag=True, help="Skip polish step")
def demo(series, batch, parallel, skip_polish):
    """Generate demo cards."""
    click.echo(f"Generating demo cards: series={series}, batch={batch}")
    # TODO: Wire up to pipeline logic
    raise NotImplementedError("demo command not yet implemented")


@cli.command("fixed-elements")
@click.option("--card-dir", required=True, help="Card directory whose rendered face receives the deterministic fixed elements")
def fixed_elements(card_dir):
    """Stamp the stat pips, type pill, rarity chip, number, and series footer deterministically."""
    from pathlib import Path

    from hypertext.cards.fixed_elements import apply_fixed_elements

    provenance = apply_fixed_elements(Path(card_dir))
    click.echo(json.dumps({"contract": provenance["contract"], "regions": {k: v.get("offset") for k, v in provenance["regions"].items()}, "face_sha256_after": provenance["face_sha256_after"]}, sort_keys=True))


@cli.command("lemma-audit")
@click.option("--series", required=True, help="Series directory (contains cards/)")
def lemma_audit(series):
    """Report every pair of cards that share a Hebrew lemma, a Greek lemma, a Hebrew root, or an English stem."""
    from hypertext.cards.lemma_uniqueness import audit_series

    conflicts = audit_series(series)
    for c in conflicts:
        click.echo(f"{c['card']} <> {c['with']}: {c['kind']} - {c['detail']}")
    click.echo(f"{len(conflicts)} conflict(s)")
    if conflicts:
        raise SystemExit(1)


@cli.command("ability-audit")
@click.option("--series", required=True, help="Series directory (contains cards/)")
@click.option("--show", is_flag=True, help="Print every card's shape signature")
def ability_audit(series, show):
    """Report every group of cards whose abilities share one shape (core motion + qualifiers)."""
    from hypertext.cards.ability_shape import ability_signature, audit_series, load_series_abilities, signature_key

    if show:
        for label, text in load_series_abilities(series):
            click.echo(f"{label:18s} {signature_key(ability_signature(text))}")
    groups = audit_series(series)
    for g in groups:
        click.echo(f"{' = '.join(g['cards'])}: {g['shape']}")
    click.echo(f"{len(groups)} shared shape(s)")
    if groups:
        raise SystemExit(1)


@cli.command()
@click.option("--card-dir", required=True, help="Path to card directory")
@click.option("--threshold", type=float, default=0.7, help="Quality threshold")
@click.option("--describe-only", is_flag=True, help="Only describe, don't score")
def review(card_dir, threshold, describe_only):
    """Review a card for quality."""
    click.echo(f"Reviewing card: {card_dir}")
    # TODO: Wire up to review logic
    raise NotImplementedError("review command not yet implemented")


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
    """Reject noncanonical stat pips or a noncanonical printed +CARD cost."""
    from pathlib import Path

    from hypertext.cards.cost_indicator_gate import (
        CostIndicatorGateError,
        inspect_cost_indicator,
    )
    from hypertext.cards.stat_pip_gate import (
        StatPipGateError,
        defect_summary,
        inspect_card_stat_pips,
    )
    from hypertext.cards.template_matrix import resolve_template_record

    directory = Path(card_dir)
    destination = Path(report_path) if report_path else directory / "outputs" / "visual-gate.json"
    candidate_file = Path(candidate) if candidate else directory / "outputs" / "card_1024x1536.png"
    try:
        result = inspect_card_stat_pips(
            directory,
            candidate_path=candidate_file,
            report_path=destination,
        )
    except StatPipGateError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        card = json.loads((directory / "card.json").read_text(encoding="utf-8"))
        content = card["content"]
        record = resolve_template_record(
            str(content["CARD_TYPE"]).upper(),
            str(content["RARITY_TEXT"]).upper(),
            verify=True,
        )
        cost = inspect_cost_indicator(candidate_file, record["path"], card)
    except (CostIndicatorGateError, OSError, KeyError, ValueError) as exc:
        raise click.ClickException(f"cost indicator gate failed: {exc}") from exc

    from hypertext.cards.rarity_chip_gate import RarityChipGateError, inspect_rarity_chip

    try:
        chip = inspect_rarity_chip(candidate_file, Path(record["path"]), card)
    except (RarityChipGateError, OSError) as exc:
        raise click.ClickException(f"rarity chip gate failed: {exc}") from exc

    combined = {
        "contract": result["contract"],
        "passed": bool(result["passed"]) and bool(cost["passed"]) and bool(chip["passed"]),
        "report": str(destination),
        "defects": list(result["defects"]) + list(cost["defects"]) + list(chip["defects"]),
        "cost_indicator": {
            "contract": cost["contract"],
            "passed": cost["passed"],
            "observed": cost.get("observed"),
        },
        "rarity_chip": {
            "contract": chip["contract"],
            "passed": chip["passed"],
            "observed": chip.get("observed"),
        },
    }
    try:
        report = json.loads(destination.read_text(encoding="utf-8"))
        report["stat_pips"] = {"passed": result["passed"], "defects": result["defects"]}
        report["cost_indicator"] = cost
        report["rarity_chip"] = chip
        report["passed"] = combined["passed"]
        destination.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    except (OSError, ValueError):
        pass
    click.echo(json.dumps(combined, sort_keys=True, default=str))
    if not combined["passed"]:
        pip_summary = defect_summary(result) if not result["passed"] else ""
        cost_summary = "; ".join(d["code"] for d in cost["defects"]) if not cost["passed"] else ""
        chip_summary = "; ".join(d["code"] for d in chip["defects"]) if not chip["passed"] else ""
        raise click.ClickException(
            "visual gate rejected candidate: "
            + "; ".join(part for part in (pip_summary, cost_summary, chip_summary) if part)
        )


@cli.command()
@click.option("--series", required=True, help="Path to series directory")
@click.option("--out-dir", default="_site", help="Output directory")
def gallery(series, out_dir):
    """Build static gallery site."""
    click.echo(f"Building gallery: series={series}, out={out_dir}")
    # TODO: Wire up to gallery builder
    raise NotImplementedError("gallery command not yet implemented")


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
    click.echo(f"Applying watermark: {card_dir}")
    # TODO: Wire up to watermark apply
    raise NotImplementedError("watermark apply not yet implemented")


@watermark.command("verify")
@click.option("--card-dir", required=True, help="Path to card directory")
@click.option("--svg", help="Path to watermark SVG (default: card_dir/watermark.svg)")
def watermark_verify(card_dir, svg):
    """Verify watermark authenticity."""
    click.echo(f"Verifying watermark: {card_dir}")
    # TODO: Wire up to watermark verify
    raise NotImplementedError("watermark verify not yet implemented")


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
    click.echo(f"LOT phase: series={series}, phase={phase}")
    # TODO: Wire up to lot generation
    raise NotImplementedError("lot command not yet implemented")


if __name__ == "__main__":
    cli()
