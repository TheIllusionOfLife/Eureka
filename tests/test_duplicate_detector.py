import unittest

from madspark.utils.duplicate_detector import (
    DuplicateDetector,
    TextProcessor,
)
from madspark.utils.models import BookmarkedIdea


class TestDuplicateDetector(unittest.TestCase):
    def setUp(self):
        self.detector = DuplicateDetector()

    def test_text_processor_normalize(self):
        # TextProcessor.normalize_text is a static method
        text = "  Hello   World!  "
        normalized = TextProcessor.normalize_text(text)
        self.assertEqual(normalized, "hello world")

    def test_text_processor_keywords(self):
        # TextProcessor.extract_keywords is a static method
        text = "The quick brown fox jumps over the lazy dog"
        keywords = TextProcessor.extract_keywords(text)
        # 'over' is not in the stop words list in the code
        expected = {"quick", "brown", "fox", "jumps", "over", "lazy", "dog"}
        self.assertEqual(keywords, expected)

    def test_calculate_similarity_identical(self):
        text = "This is a test idea."
        score = self.detector.calculate_similarity(text, text)
        self.assertEqual(score, 1.0)

    def test_calculate_similarity_different(self):
        text1 = "This is a test idea."
        text2 = "Something completely different."
        score = self.detector.calculate_similarity(text1, text2)
        # Using assertLess instead of checking specifically for 0 because semantic similarity might be non-zero
        self.assertLess(score, 0.5)

    def test_find_duplicates_match(self):
        existing = [
            BookmarkedIdea(
                id="1",
                text="This is a test idea.",
                topic="Testing",
                context="",
                score=0,
                critique="",
                advocacy="",
                skepticism="",
                bookmarked_at="",
                tags=[],
            ),
            BookmarkedIdea(
                id="2",
                text="Something else entirely.",
                topic="Other",
                context="",
                score=0,
                critique="",
                advocacy="",
                skepticism="",
                bookmarked_at="",
                tags=[],
            ),
        ]

        # Test exact match
        duplicates = self.detector.find_duplicates(
            "This is a test idea.", "Testing", existing
        )
        self.assertTrue(len(duplicates) > 0)
        self.assertEqual(duplicates[0].bookmark_id, "1")
        self.assertAlmostEqual(duplicates[0].similarity_score, 1.0)

    def test_find_duplicates_no_match(self):
        existing = [
            BookmarkedIdea(
                id="1",
                text="This is a test idea.",
                topic="Testing",
                context="",
                score=0,
                critique="",
                advocacy="",
                skepticism="",
                bookmarked_at="",
                tags=[],
            ),
            BookmarkedIdea(
                id="2",
                text="Something else entirely.",
                topic="Other",
                context="",
                score=0,
                critique="",
                advocacy="",
                skepticism="",
                bookmarked_at="",
                tags=[],
            ),
        ]

        # Test no match
        duplicates = self.detector.find_duplicates("New unique idea", "New", existing)
        self.assertEqual(len(duplicates), 0)


if __name__ == "__main__":
    unittest.main()
