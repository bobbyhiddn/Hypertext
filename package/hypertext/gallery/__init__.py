"""Gallery and deck assembly for Hypertext."""

from hypertext.gallery.builder import (
    build_gallery,
    build_card_html,
    build_series_card_html,
    load_card_meta,
)
from hypertext.gallery.deck import (
    assemble_deck,
    find_cards,
    load_card,
    extract_card_info,
    generate_decklist,
    save_decklist,
)

__all__ = [
    # builder.py
    "build_gallery",
    "build_card_html",
    "build_series_card_html",
    "load_card_meta",
    # deck.py
    "assemble_deck",
    "find_cards",
    "load_card",
    "extract_card_info",
    "generate_decklist",
    "save_decklist",
]
