"""Tests for sector taxonomy normalization, unified Gemini prompt, and response parsing."""

import unittest
from app.constants.sectors import (
    FALLBACK_SECTOR,
    PREDEFINED_SECTORS,
    format_sectors_for_prompt,
    normalize_sector,
)
from app.models.stock import Stock
from app.services.gemini_tagger import GeminiTagger, UNIFIED_TAGGING_PROMPT


class TestSectorClassification(unittest.TestCase):
    def test_sector_taxonomy_integrity(self):
        """Verify predefined sectors are unique and contain required fallback."""
        self.assertGreater(len(PREDEFINED_SECTORS), 50)
        self.assertEqual(len(PREDEFINED_SECTORS), len(set(PREDEFINED_SECTORS)), "Duplicates found in sector list")
        self.assertIn(FALLBACK_SECTOR, PREDEFINED_SECTORS)

        prompt_text = format_sectors_for_prompt()
        self.assertIn("Auto Ancillary", prompt_text)
        self.assertIn("IT Large Cap", prompt_text)
        self.assertNotIn(FALLBACK_SECTOR, prompt_text)

    def test_normalize_sector_exact_and_case_insensitive(self):
        """Verify exact and case-insensitive matching."""
        self.assertEqual(normalize_sector("Auto Ancillary"), "Auto Ancillary")
        self.assertEqual(normalize_sector("auto ancillary"), "Auto Ancillary")
        self.assertEqual(normalize_sector("AUTO ANCILLARY"), "Auto Ancillary")
        self.assertEqual(normalize_sector("  it large cap  "), "IT Large Cap")
        self.assertEqual(normalize_sector("Pharma - API & CRAMS"), "Pharma - API & CRAMS")

    def test_normalize_sector_fuzzy_matching(self):
        """Verify fuzzy matching on slight plurals or typos."""
        # "Auto Ancillaries" -> "Auto Ancillary"
        self.assertEqual(normalize_sector("Auto Ancillaries"), "Auto Ancillary")
        # "Plastic Pipe" -> "Plastic Pipes"
        self.assertEqual(normalize_sector("Plastic Pipe"), "Plastic Pipes")
        # "Packaged Meats" -> "Packaged Meat"
        self.assertEqual(normalize_sector("Packaged Meats"), "Packaged Meat")

    def test_normalize_sector_fallback(self):
        """Verify fallback when sector is completely unknown or empty."""
        self.assertEqual(normalize_sector(None), FALLBACK_SECTOR)
        self.assertEqual(normalize_sector(""), FALLBACK_SECTOR)
        self.assertEqual(normalize_sector("Completely Fictional Random Industry 12345"), FALLBACK_SECTOR)

    def test_parse_single_stock_batch(self):
        """Verify unified parser parses a single-stock JSON response."""
        stock = Stock(id=1, symbol="TATAMOTORS", name="Tata Motors", sector=None)
        raw = """{
            "TATAMOTORS": {
                "sector": "Auto OEM",
                "tags": ["commercial vehicles", "ev passenger cars", "automobiles"]
            }
        }"""
        results = GeminiTagger._parse_tags_batch(raw, [stock])
        self.assertIn("TATAMOTORS", results)
        self.assertEqual(results["TATAMOTORS"]["sector"], "Auto OEM")
        self.assertEqual(results["TATAMOTORS"]["tags"], ["commercial vehicles", "ev passenger cars", "automobiles"])

    def test_parse_batch_result_with_markdown_fences(self):
        """Verify parsing of batch Gemini responses wrapped in markdown fences."""
        stocks = [
            Stock(id=1, symbol="TATAMOTORS", name="Tata Motors", sector="Auto OEM"),
            Stock(id=2, symbol="TCS", name="Tata Consultancy Services", sector=None),
            Stock(id=3, symbol="UNKNOWN", name="Unknown Co", sector=None),
        ]

        raw_batch = """```json
        {
            "TATAMOTORS": {
                "sector": "Auto OEM",
                "tags": ["commercial vehicles", "ev passenger cars", "automobiles"]
            },
            "TCS": {
                "sector": "it large cap",
                "tags": ["it consulting", "cloud computing", "enterprise software"]
            }
        }
        ```"""

        results = GeminiTagger._parse_tags_batch(raw_batch, stocks)
        self.assertIn("TATAMOTORS", results)
        self.assertEqual(results["TATAMOTORS"]["sector"], "Auto OEM")
        self.assertEqual(results["TATAMOTORS"]["tags"], ["commercial vehicles", "ev passenger cars", "automobiles"])

        self.assertIn("TCS", results)
        self.assertEqual(results["TCS"]["sector"], "IT Large Cap")
        self.assertEqual(results["TCS"]["tags"], ["it consulting", "cloud computing", "enterprise software"])

        # Missing stock gets fallback
        self.assertIn("UNKNOWN", results)
        self.assertEqual(results["UNKNOWN"]["sector"], FALLBACK_SECTOR)

    def test_unified_prompt_formatting(self):
        """Verify UNIFIED_TAGGING_PROMPT formats correctly without errors."""
        stocks_data = "- Symbol: RELIANCE, Name: Reliance Industries, Sector: Unknown, LTP: 2900, Change: 1.2%"
        prompt = UNIFIED_TAGGING_PROMPT.format(
            screener_name="Top Gainers",
            stocks_data=stocks_data,
            predefined_sectors=format_sectors_for_prompt(),
        )
        self.assertIn("RELIANCE", prompt)
        self.assertIn("Oil Refiners", prompt)
        self.assertIn("Top Gainers", prompt)


if __name__ == "__main__":
    unittest.main()
