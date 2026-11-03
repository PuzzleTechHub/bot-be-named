import unittest

from utils.formula_utils import hyperlink


class HyperlinkTest(unittest.TestCase):
    def test_ordinary_name_is_unchanged(self):
        self.assertEqual(
            hyperlink("https://example.com/sheet", "A Puzzle"),
            '=HYPERLINK("https://example.com/sheet", "A Puzzle")',
        )

    def test_quoted_name(self):
        self.assertEqual(
            hyperlink("https://example.com/sheet", 'A "Puzzle"'),
            '=HYPERLINK("https://example.com/sheet", "A ""Puzzle""")',
        )

    def test_adjacent_quotes_are_preserved(self):
        self.assertEqual(hyperlink("url", '""'), '=HYPERLINK("url", """""")')

    def test_quote_in_url(self):
        self.assertEqual(
            hyperlink('https://example.com/"puzzle"', "Name"),
            '=HYPERLINK("https://example.com/""puzzle""", "Name")',
        )

    def test_formula_like_name_remains_a_string(self):
        self.assertEqual(
            hyperlink("url", '", IMPORTXML("other", "path"), "'),
            '=HYPERLINK("url", """, IMPORTXML(""other"", ""path""), """)',
        )

    def test_empty_label(self):
        self.assertEqual(hyperlink("url", ""), '=HYPERLINK("url", "")')

    def test_unicode_and_apostrophes_are_preserved(self):
        self.assertEqual(hyperlink("url", "L'été 🧩"), '=HYPERLINK("url", "L\'été 🧩")')


if __name__ == "__main__":
    unittest.main()
