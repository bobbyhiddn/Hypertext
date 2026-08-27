"""The Game Crafter API integration for Hypertext."""

from .client import TGCClient
from .processor import prepare_for_print, add_bleed, validate_dimensions

__all__ = [
    "TGCClient",
    "prepare_for_print",
    "add_bleed",
    "validate_dimensions",
]
