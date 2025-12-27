import os
import sys
import yaml
import shutil
import argparse
from pathlib import Path
from datetime import datetime

try:
    import markdown
except ImportError:
    markdown = None

def parse_args():
    parser = argparse.ArgumentParser(description="Build static gallery site")
    parser.add_argument(
        "--series-dir",
        type=Path,
        default=Path("series"),
        help="Path to series root (recommended: 'series') OR a single series dir (e.g. 'series/2026-Q1')",
    )
    parser.add_argument("--out-dir", type=Path, default=Path("_site"), help="Output directory for static site")
    parser.add_argument("--index-template", type=Path, default=Path("templates/gallery_index_template.html"), help="Root index HTML template")
    parser.add_argument("--series-template", type=Path, default=Path("templates/gallery_series_template.html"), help="Per-series HTML template")
    parser.add_argument("--rules-template", type=Path, default=Path("templates/gallery_rules_template.html"), help="Rules page HTML template")
    parser.add_argument("--rules-md", type=Path, default=Path("docs/rules.md"), help="Source markdown for rules")
    parser.add_argument("--assets-css", type=Path, default=Path("templates/gallery_assets.css"), help="CSS asset source")
    parser.add_argument("--assets-js", type=Path, default=Path("templates/gallery_assets.js"), help="JS asset source")
    return parser.parse_args()

def load_card_meta(card_dir: Path) -> dict | None:
    meta_path = card_dir / "meta.yml"
    if not meta_path.exists():
        return None

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading {meta_path}: {e}")
        return None


def _read_text(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _is_series_dir(p: Path) -> bool:
    return (p / "cards").exists() and (p / "deck").exists()


def _find_series_dirs(series_dir: Path) -> list[Path]:
    # If the provided path is already a series directory, build just that one.
    if _is_series_dir(series_dir):
        return [series_dir]

    # Otherwise, treat it as a root containing series subfolders.
    if not series_dir.exists():
        return []

    out: list[Path] = []
    for p in sorted(series_dir.iterdir()):
        if p.is_dir() and _is_series_dir(p):
            out.append(p)
    return out


def _safe_int(v, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def build_card_html(meta: dict, image_rel: str) -> str:
    # Safely get values with defaults
    number = meta.get("number", "???")
    word = meta.get("word", "???")
    rarity = meta.get("rarity", "COMMON").upper()
    card_type = meta.get("card_type", "NOUN")
    gloss = meta.get("gloss", "")
    
    rarity_cls = rarity.lower()
    number_int = _safe_int(number, 0)

    return (
        f"<article class=\"card\" data-card data-number=\"{number_int}\" "
        f"data-word=\"{word}\" data-gloss=\"{gloss}\" data-rarity=\"{rarity}\" data-type=\"{card_type}\">"
        f"<img src=\"{image_rel}\" alt=\"{word}\" loading=\"lazy\" />"
        f"<div class=\"card-meta\">"
        f"<div class=\"card-title\">#{number} {word}</div>"
        f"<div class=\"card-sub\">"
        f"<span class=\"muted\">{card_type}</span>"
        f"<span class=\"tag {rarity_cls}\">{rarity}</span>"
        f"</div>"
        f"</div>"
        f"</article>"
    )


def build_series_card_html(*, series_name: str, href: str, cover_rel: str, card_count: int) -> str:
    cover_html = (
        f"<img class=\"series-cover\" src=\"{cover_rel}\" alt=\"{series_name} cover\" loading=\"lazy\" />"
        if cover_rel
        else "<div class=\"series-cover\" aria-hidden=\"true\"></div>"
    )
    return (
        f"<div class=\"series-card\">"
        f"<a href=\"{href}\">"
        + cover_html
        + f"<div class=\"series-meta\">"
        f"<div class=\"series-title\">{series_name}</div>"
        f"<div class=\"series-sub\">{card_count} cards</div>"
        f"<div class=\"series-badges\">"
        f"<div class=\"pill\">Open</div>"
        f"</div>"
        f"</div>"
        f"</a>"
        f"</div>"
    )


def _copy_assets(*, out_dir: Path, css_src: Path, js_src: Path) -> None:
    assets_dir = out_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(css_src, assets_dir / "gallery.css")
    shutil.copy2(js_src, assets_dir / "gallery.js")


def _collect_series_cards(series_dir: Path) -> list[dict]:
    cards_dir = series_dir / "cards"
    valid_cards: list[dict] = []
    if not cards_dir.exists():
        return valid_cards

    for card_dir in sorted(cards_dir.iterdir()):
        if not card_dir.is_dir():
            continue

        meta = load_card_meta(card_dir)
        if not meta:
            continue

        img_src = card_dir / "outputs" / "card_1024x1536.png"
        if not img_src.exists():
            continue

        valid_cards.append({"dir": card_dir, "meta": meta, "img_src": img_src})

    valid_cards.sort(key=lambda x: str(x["meta"].get("number", "999")))
    return valid_cards

def _build_rules_page(*, rules_md_path: Path, template_path: Path, out_dir: Path, generation_date: str) -> None:
    if not rules_md_path.exists() or not template_path.exists():
        print(f"Skipping rules page: missing {rules_md_path} or {template_path}")
        return

    if markdown is None:
        print("Skipping rules page: markdown package not installed")
        return

    md_text = _read_text(rules_md_path)
    # Convert MD to HTML with tables support
    html_content = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

    template = _read_text(template_path)
    page = (
        template.replace("<!-- RULES_CONTENT_INJECTION_POINT -->", html_content)
        .replace("{GENERATION_DATE}", generation_date)
    )

    rules_out_dir = out_dir / "rules"
    rules_out_dir.mkdir(parents=True, exist_ok=True)
    _write_text(rules_out_dir / "index.html", page)
    print(f"Built rules page at {rules_out_dir / 'index.html'}")


def main():
    args = parse_args()

    # Validate inputs
    for p in [args.index_template, args.series_template, args.assets_css, args.assets_js, args.rules_template]:
        if not p.exists():
            print(f"Missing required gallery file: {p}")
            return 1

    series_dirs = _find_series_dirs(args.series_dir)
    if not series_dirs:
        print(f"No series directories found under: {args.series_dir}")
        return 1

    # Prepare output directory
    if args.out_dir.exists():
        shutil.rmtree(args.out_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    _copy_assets(out_dir=args.out_dir, css_src=args.assets_css, js_src=args.assets_js)

    # Build per-series pages
    index_series_cards: list[str] = []
    generation_date = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    for series_path in series_dirs:
        series_name = series_path.name
        cards = _collect_series_cards(series_path)

        print(f"Scanning {series_path / 'cards'}...")
        for card in cards:
            print(f"Processed #{card['meta'].get('number')} {card['meta'].get('word')}")

        series_out_dir = args.out_dir / "series" / series_name
        images_dir = series_out_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        card_html: list[str] = []
        cover_rel = ""

        for i, card in enumerate(cards):
            slug = card["dir"].name
            img_filename = f"{slug}.png"
            img_dest = images_dir / img_filename
            shutil.copy2(card["img_src"], img_dest)

            # relative from /series/<name>/index.html
            rel = f"./images/{img_filename}"
            card_html.append(build_card_html(card["meta"], rel))

            if i == 0:
                cover_rel = rel

        if not cover_rel:
            cover_rel = ""

        series_template = _read_text(args.series_template)
        series_page = (
            series_template.replace("{SERIES_NAME}", series_name)
            .replace("<!-- CARDS_INJECTION_POINT -->", "\n".join(card_html))
            .replace("{GENERATION_DATE}", generation_date)
        )

        _write_text(series_out_dir / "index.html", series_page)

        # Add series card to root index
        index_series_cards.append(
            build_series_card_html(
                series_name=series_name,
                href=f"./series/{series_name}/",
                cover_rel=(f"./series/{series_name}/{cover_rel.lstrip('./')}" if cover_rel else ""),
                card_count=len(cards),
            )
        )

    # Root index: series-first view
    index_template = _read_text(args.index_template)
    index_page = (
        index_template.replace("<!-- SERIES_INJECTION_POINT -->", "\n".join(index_series_cards))
        .replace("{GENERATION_DATE}", generation_date)
    )
    _write_text(args.out_dir / "index.html", index_page)

    # Convenience /series/ index (redirect to root)
    _write_text(
        args.out_dir / "series" / "index.html",
        "<!doctype html><meta charset=\"utf-8\"><meta http-equiv=\"refresh\" content=\"0; url=../index.html\">",
    )

    # Build rules page
    _build_rules_page(
        rules_md_path=args.rules_md,
        template_path=args.rules_template,
        out_dir=args.out_dir,
        generation_date=generation_date
    )

    print(f"Gallery built at {args.out_dir / 'index.html'} with {len(series_dirs)} series")
    return 0

if __name__ == "__main__":
    sys.exit(main())
