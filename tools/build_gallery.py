import os
import sys
import yaml
import shutil
import argparse
from pathlib import Path
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(description="Build static gallery site")
    parser.add_argument("--series-dir", type=Path, default=Path("series/2026-Q1"), help="Path to series directory")
    parser.add_argument("--out-dir", type=Path, default=Path("_site"), help="Output directory for static site")
    parser.add_argument("--template", type=Path, default=Path("templates/gallery_template.html"), help="HTML template path")
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

def build_card_html(meta: dict, image_filename: str) -> str:
    # Safely get values with defaults
    number = meta.get("number", "???")
    word = meta.get("word", "???")
    rarity = meta.get("rarity", "COMMON").upper()
    card_type = meta.get("card_type", "NOUN")
    gloss = meta.get("gloss", "")
    
    # CSS class for rarity
    rarity_class = f"rarity-{rarity.lower()}"
    
    return f"""
        <div class="card-item" data-rarity="{rarity}" data-type="{card_type}">
            <img src="images/{image_filename}" alt="{word}" class="card-image" loading="lazy">
            <div class="card-meta">
                <div class="card-title">#{number} {word}</div>
                <div class="card-info">
                    <span class="type-tag">{card_type}</span>
                    <span class="rarity-tag {rarity_class}">{rarity}</span>
                </div>
                <div class="card-gloss" style="font-size: 0.8em; color: #666; margin-top: 5px;">{gloss}</div>
            </div>
        </div>
    """

def main():
    args = parse_args()
    
    if not args.series_dir.exists():
        print(f"Series directory not found: {args.series_dir}")
        return 1
        
    if not args.template.exists():
        print(f"Template not found: {args.template}")
        return 1
        
    # Prepare output directory
    images_dir = args.out_dir / "images"
    if args.out_dir.exists():
        shutil.rmtree(args.out_dir)
    args.out_dir.mkdir(parents=True)
    images_dir.mkdir()
    
    # Find and process cards
    cards_dir = args.series_dir / "cards"
    cards = []
    
    print(f"Scanning {cards_dir}...")
    
    # Collect valid cards
    valid_cards = []
    for card_dir in sorted(cards_dir.iterdir()):
        if not card_dir.is_dir():
            continue
            
        meta = load_card_meta(card_dir)
        if not meta:
            continue
            
        img_src = card_dir / "outputs" / "card_1024x1536.png"
        if not img_src.exists():
            print(f"Skipping {card_dir.name}: No image found")
            continue
            
        valid_cards.append({
            "dir": card_dir,
            "meta": meta,
            "img_src": img_src
        })
        
    # Sort by number
    valid_cards.sort(key=lambda x: str(x["meta"].get("number", "999")))
    
    html_fragments = []
    
    for card in valid_cards:
        slug = card["dir"].name
        img_filename = f"{slug}.png"
        img_dest = images_dir / img_filename
        
        # Copy image
        shutil.copy2(card["img_src"], img_dest)
        
        # Build HTML
        html_fragments.append(build_card_html(card["meta"], img_filename))
        print(f"Processed #{card['meta'].get('number')} {card['meta'].get('word')}")
        
    # Read template
    with open(args.template, "r", encoding="utf-8") as f:
        template_content = f.read()
        
    # Inject content
    final_html = template_content.replace(
        "<!-- CARDS_INJECTION_POINT -->", 
        "\n".join(html_fragments)
    ).replace(
        "{GENERATION_DATE}", 
        datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    )
    
    # Write index.html
    out_path = args.out_dir / "index.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(final_html)
        
    print(f"Gallery built at {out_path} with {len(valid_cards)} cards")
    return 0

if __name__ == "__main__":
    sys.exit(main())
