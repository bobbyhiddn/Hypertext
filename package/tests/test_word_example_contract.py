import copy
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from hypertext.cards.example_contract import (
    ExampleContractError, canonical_projection, load_contract, validate_projection,
)
from scripts import build_word_example_set as builder

ROOT = Path(__file__).resolve().parents[2]


EVIDENCE_PRESENT = (ROOT / "templates/archive").exists()


class WordExampleContractTests(unittest.TestCase):
    def test_matrix_projects_exact_canonical_fields(self):
        contract = load_contract(ROOT)
        seen = set()
        card_id = 0
        for kind, slugs in contract["variants"].items():
            for rarity in contract["rarities"]:
                for variant, slug in enumerate(slugs, 1):
                    card_id += 1
                    content, source = canonical_projection(ROOT, contract, kind, variant)
                    validate_projection(ROOT, contract, {"id": card_id, "type": kind,
                        "variant": variant, "rarity": rarity, "canonical_source": source,
                        "authoritative_content": content})
                    seen.add((kind, rarity, variant, slug))
        self.assertEqual(len(seen), 60)

    def test_decorative_translation_is_rejected(self):
        contract = load_contract(ROOT)
        content, source = canonical_projection(ROOT, contract, "verb", 1)
        bad = copy.deepcopy(content)
        bad["HEBREW"] = "אוֹר"
        with self.assertRaisesRegex(ExampleContractError, "approximate/decorative"):
            validate_projection(ROOT, contract, {"id": 13, "type": "verb", "variant": 1,
                "rarity": "common", "canonical_source": source, "authoritative_content": bad})

    def test_unowned_authoritative_field_is_rejected(self):
        contract = load_contract(ROOT)
        content, source = canonical_projection(ROOT, contract, "noun", 1)
        content["DECORATIVE_TRANSLATION"] = "invented"
        with self.assertRaisesRegex(ExampleContractError, "field ownership"):
            validate_projection(ROOT, contract, {"id": 1, "type": "noun", "variant": 1,
                "rarity": "common", "canonical_source": source,
                "authoritative_content": content})

    def test_known_babel_source_defects_are_not_selected(self):
        contract = load_contract(ROOT)
        selected = {slug for slugs in contract["variants"].values() for slug in slugs}
        excluded = {item["card"] for item in contract["source_defects_excluded"]}
        self.assertTrue(excluded.isdisjoint(selected))

    @unittest.skipUnless(EVIDENCE_PRESENT, "cold evidence archive not present - run scripts/fetch_evidence.sh")
    def test_generator_anchors_every_card_to_accepted_see_v4(self):
        record = builder.source_records()[0]
        refs, roles = builder.reference_inputs(record)
        self.assertEqual(refs[1], builder.VISUAL_BENCHMARK)
        self.assertEqual(roles[1], "accepted SEE v4 visual benchmark")
        self.assertEqual(refs[3], builder.LANGUAGE_BENCHMARK)
        self.assertEqual(roles[3], "operator-accepted printed SEE Languages-region benchmark")
        self.assertEqual(len(refs), 4)
        self.assertTrue(all(path.is_file() for path in refs))
        self.assertIn("Never print placeholder", builder.card_data(record)["model_prompt"])

    def test_reference_line_contract_keeps_all_internal_bullets(self):
        value = "Gen 11 • Deut 28 • Ps 147 • Jer 31 • Zech 13"
        rendered = builder.reference_line_contract("OT", value)
        self.assertIn("Line 1 is 'OT Refs: Gen 11 • Deut 28 •'", rendered)
        self.assertIn("Line 2 is 'Ps 147 • Jer 31 • Zech 13'", rendered)
        self.assertIn("Neither line begins with a bullet", rendered)

    def test_previous_raster_is_reused_only_when_all_input_hashes_match(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = {
                "id": 1,
                "input_contract_version": 1,
                "visual_descriptor_version": 2,
                "render_contract_version": builder.RENDER_CONTRACT_VERSION,
                "visual_benchmark_version": builder.VISUAL_BENCHMARK_VERSION,
            }
            for key in ("card_json", "prompt", "request", "output"):
                path = root / f"{key}.dat"
                path.write_text(key, encoding="utf-8")
                record[key] = path.name
                record[f"{key.removesuffix('_json')}_sha256"] = builder.sha(path)
            with mock.patch.object(builder, "ROOT", root):
                self.assertTrue(builder.valid_previous_record(record))
                (root / record["prompt"]).write_text("changed", encoding="utf-8")
                self.assertFalse(builder.valid_previous_record(record))


if __name__ == "__main__":
    unittest.main()
