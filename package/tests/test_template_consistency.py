"""Pixel-preservation and stable-reference regressions for card rendering."""

import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

from hypertext.cards.polish import finalize_card
from hypertext.pipeline import daily


class FinalizationTests(unittest.TestCase):
    def test_finalization_is_byte_identical_and_preserves_subtitle_edges(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source.png"
            output = Path(td) / "nested" / "output.png"
            image = Image.new("RGB", (1024, 1536), "#f3e7c8")
            # High-contrast pixels model the antialiased subtitle boundary. A
            # decode/resample/generative pass would not preserve this digest.
            image.putpixel((511, 105), (17, 17, 17))
            image.putpixel((512, 105), (119, 113, 97))
            image.save(source, "PNG")
            before = hashlib.sha256(source.read_bytes()).digest()

            finalize_card(str(source), str(output))

            self.assertEqual(hashlib.sha256(output.read_bytes()).digest(), before)

    def test_in_place_finalization_does_not_rewrite_file(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "card.png"
            source.write_bytes(b"already validated image bytes")
            stat_before = source.stat()
            finalize_card(str(source), str(source))
            self.assertEqual(source.read_bytes(), b"already validated image bytes")
            self.assertEqual(source.stat().st_mtime_ns, stat_before.st_mtime_ns)


class StableReferenceTests(unittest.TestCase):
    def test_default_references_do_not_depend_on_prior_series_cards(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(
            daily, "_find_matching_cards", side_effect=AssertionError("series drift")
        ), mock.patch.object(daily, "_get_subtype_template", return_value=None), \
             mock.patch.object(daily.Path, "exists", return_value=False):
            refs, labels, fix = daily._build_style_refs(
                Path(td), target_rarity="COMMON", target_type="NOUN"
            )
        self.assertEqual((refs, labels, fix), ([], {}, False))


if __name__ == "__main__":
    unittest.main()
