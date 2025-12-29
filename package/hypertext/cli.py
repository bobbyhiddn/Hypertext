#!/usr/bin/env python3
"""Hypertext CLI - Biblical word-study trading card game toolkit."""

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


@cli.command()
@click.option("--card-dir", required=True, help="Path to card directory")
@click.option("--threshold", type=float, default=0.7, help="Quality threshold")
@click.option("--describe-only", is_flag=True, help="Only describe, don't score")
def review(card_dir, threshold, describe_only):
    """Review a card for quality."""
    click.echo(f"Reviewing card: {card_dir}")
    # TODO: Wire up to review logic
    raise NotImplementedError("review command not yet implemented")


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
