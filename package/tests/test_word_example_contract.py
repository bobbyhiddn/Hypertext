import copy
import unittest
from pathlib import Path

from hypertext.cards.example_contract import (
    ExampleContractError, canonical_projection, load_contract, validate_projection,
)

ROOT = Path(__file__).resolve().parents[2]


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


if __name__ == "__main__":
    unittest.main()
