import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hash_table import HashTable, LinearProbingHashTable  # noqa: E402
from shortener import Shortener  # noqa: E402


class ShortenerContract:
    table_class = None

    def setUp(self):
        self.s = Shortener(table_class=self.table_class)

    def test_first_codes(self):
        self.assertEqual(self.s.shorten("https://a.com"), "1")
        self.assertEqual(self.s.shorten("https://b.com"), "2")

    def test_same_url_same_code(self):
        c1 = self.s.shorten("https://a.com/x")
        c2 = self.s.shorten("https://a.com/x")
        self.assertEqual(c1, c2)
        self.assertEqual(self.s.shorten("https://b.com"), "2")  # 번호를 낭비하지 않는다
        self.assertEqual(len(self.s), 2)

    def test_round_trip(self):
        url = "http://example.com/path?q=1&r=가#frag"
        self.assertEqual(self.s.expand(self.s.shorten(url)), url)

    def test_unknown_code(self):
        self.assertIsNone(self.s.expand("1"))
        self.s.shorten("https://a.com")
        self.assertIsNone(self.s.expand("2"))

    def test_invalid_code(self):
        self.s.shorten("https://a.com")
        for bad in ("", "!!", "a b", "-1", None, 1):
            self.assertIsNone(self.s.expand(bad))

    def test_invalid_urls(self):
        bad = ["", "   ", "example.com", "ftp://a.com", "http://", "https://",
               "http://a .com", "http://a.com/\nx", "javascript:alert(1)",
               "https://a.com/" + "x" * 2040]
        for url in bad:
            with self.assertRaises(ValueError, msg=repr(url)):
                self.s.shorten(url)
        for url in (None, 123):
            with self.assertRaises(ValueError):
                self.s.shorten(url)

    def test_max_length_ok(self):
        url = "https://a.com/" + "x" * (2048 - len("https://a.com/"))
        self.assertEqual(len(url), 2048)
        self.assertEqual(self.s.expand(self.s.shorten(url)), url)

    def test_strip_spaces(self):
        c = self.s.shorten("  https://a.com  ")
        self.assertEqual(self.s.shorten("https://a.com"), c)
        self.assertEqual(self.s.expand(c), "https://a.com")

    def test_no_normalization(self):
        self.assertNotEqual(self.s.shorten("https://a.com"), self.s.shorten("https://a.com/"))
        self.assertNotEqual(self.s.shorten("https://A.com"), self.s.shorten("https://a.com"))

    def test_hash_collision_urls_get_different_codes(self):
        # "Aa"와 "BB"는 Horner 해시가 같다. 코드는 해시가 아니라 일련번호라 달라야 한다
        c1 = self.s.shorten("https://x.com/Aa")
        c2 = self.s.shorten("https://x.com/BB")
        self.assertNotEqual(c1, c2)
        self.assertEqual(self.s.expand(c1), "https://x.com/Aa")
        self.assertEqual(self.s.expand(c2), "https://x.com/BB")

    def test_many(self):
        urls = [f"https://site{i}.com/p/{i * 7}" for i in range(1000)]
        codes = [self.s.shorten(u) for u in urls]
        self.assertEqual(codes[60], "Z")   # 61번째 URL → 61
        self.assertEqual(codes[61], "10")  # 62번째 URL → 62
        for u, c in zip(urls, codes):
            self.assertEqual(self.s.expand(c), u)


class TestShortenerChaining(ShortenerContract, unittest.TestCase):
    table_class = HashTable


class TestShortenerLinear(ShortenerContract, unittest.TestCase):
    table_class = LinearProbingHashTable


class TestShortenerDefault(unittest.TestCase):
    def test_default_is_chaining(self):
        self.assertIs(Shortener().table_class, HashTable)


if __name__ == "__main__":
    unittest.main()
