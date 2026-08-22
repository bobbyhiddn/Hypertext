"""Pixel-preservation and stable-reference regressions for card rendering."""

import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image, ImageFont

from hypertext.cards.composite import CLEANUP_REGIONS, REGIONS, _get_fonts, composite_card
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


class CompositeRendererTests(unittest.TestCase):
    ROOT = Path(__file__).parents[2]
    TEMPLATE = ROOT / "templates/card/v001/base/template_1024x1536.png"
    CARD = ROOT / "templates/example_cards/001-grace/card.json"

    def render(self, directory, name="card.png"):
        import json
        content = json.loads(self.CARD.read_text(encoding="utf-8"))["content"]
        output = Path(directory) / name
        composite_card(str(self.TEMPLATE), None, str(output), content)
        return output, content

    def test_typography_geometry_and_subtitle_are_rendered_once(self):
        fonts = _get_fonts()
        self.assertTrue(all(isinstance(font, ImageFont.FreeTypeFont) for font in fonts.values()))
        self.assertEqual(REGIONS["art_panel"], (66, 264, 910, 247))
        self.assertLess(REGIONS["gloss_subtitle"][1], REGIONS["art_panel"][1])
        with tempfile.TemporaryDirectory() as td:
            output, content = self.render(td)
            image = Image.open(output).convert("RGB")
            # Placeholder title ink is gone, while the requested subtitle has
            # a non-parchment text run in its dedicated band.
            self.assertNotEqual(image.getpixel((512, 98)), (17, 17, 17))
            subtitle = image.crop((180, 140, 844, 190))
            self.assertGreater(len(set(subtitle.get_flattened_data())), 40)
            self.assertIn("favor", content["GLOSS"])

    def test_card_facts_pips_and_borders_survive_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            output, content = self.render(td)
            source = Image.open(self.TEMPLATE).convert("RGB").resize((1024, 1536), Image.Resampling.LANCZOS)
            image = Image.open(output).convert("RGB")
            # Cleanup never reaches representative outer and panel-border pixels.
            for point in ((30, 400), (62, 510), (62, 770), (62, 1020), (62, 1425)):
                self.assertEqual(image.getpixel(point), source.getpixel(point))
            self.assertEqual([content[k] for k in ("STAT_LORE", "STAT_CONTEXT", "STAT_COMPLEXITY")], [5, 5, 2])
            for start, filled in ((108, 5), (414, 5), (721, 2)):
                centers = [image.getpixel((start + i * 52, 601)) for i in range(5)]
                self.assertEqual(sum(pixel[2] < 100 for pixel in centers), filled)
            facts = image.crop((72, 642, 952, 1218))
            self.assertGreater(len(set(facts.get_flattened_data())), 100)

    def test_revision_alignment_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            first, _ = self.render(td, "fresh.png")
            second, _ = self.render(td, "revision.png")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            for box in CLEANUP_REGIONS.values():
                self.assertGreaterEqual(box[0], 48)
                self.assertLessEqual(box[2], 984)


if __name__ == "__main__":
    unittest.main()
