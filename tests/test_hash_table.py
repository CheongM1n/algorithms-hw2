import ast
import os
import sys
import unittest

SRC = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, SRC)

import hash_table  # noqa: E402
from hash_table import HashTable, horner_hash  # noqa: E402


class TestHorner(unittest.TestCase):
    def test_empty_string(self):
        self.assertEqual(horner_hash("", 11), 0)

    def test_by_hand(self):
        # "ab": h = 97 % 11 = 9, h = (31*9 + 98) % 11 = 377 % 11 = 3
        self.assertEqual(horner_hash("ab", 11), 3)

    def test_range(self):
        for k in ("a", "hello", "https://example.com/x", "가나다"):
            for m in (1, 2, 11, 16, 4093):
                self.assertTrue(0 <= horner_hash(k, m) < m)

    def test_classic_collision(self):
        # 31*'A' + 'a' == 31*'B' + 'B'  → 어떤 M에서도 충돌
        for m in (11, 16, 4093):
            self.assertEqual(horner_hash("Aa", m), horner_hash("BB", m))


class HashTableContract:
    """해시 테이블이 지켜야 할 공통 약속. 구현 클래스마다 make()만 바꿔 돌린다."""

    def make(self, **kw):
        raise NotImplementedError

    def test_empty(self):
        t = self.make()
        self.assertEqual(len(t), 0)
        self.assertNotIn("a", t)
        with self.assertRaises(KeyError):
            t.get("a")
        found, value, _ = t.find("a")
        self.assertFalse(found)
        self.assertIsNone(value)
        self.assertEqual(t.load_factor(), 0)

    def test_put_get(self):
        t = self.make()
        t.put("a", 1)
        t.put("b", 2)
        self.assertEqual(t.get("a"), 1)
        self.assertEqual(t.get("b"), 2)
        self.assertIn("a", t)
        self.assertEqual(len(t), 2)

    def test_overwrite_keeps_len(self):
        t = self.make()
        t.put("a", 1)
        t.put("a", 99)
        self.assertEqual(t.get("a"), 99)
        self.assertEqual(len(t), 1)

    def test_empty_and_korean_keys(self):
        t = self.make()
        t.put("", "empty")
        t.put("한글", "ok")
        self.assertEqual(t.get(""), "empty")
        self.assertEqual(t.get("한글"), "ok")

    def test_none_value(self):
        t = self.make()
        t.put("a", None)
        self.assertIn("a", t)
        self.assertIsNone(t.get("a"))
        self.assertTrue(t.find("a")[0])

    def test_colliding_keys(self):
        t = self.make(capacity=11, max_load=None)
        keys = ["aj", "au", "ba", "bl", "bw", "cc"]  # 모두 M=11에서 해시값 0
        for k in keys:
            self.assertEqual(horner_hash(k, 11), 0)
        for i, k in enumerate(keys):
            t.put(k, i)
        for i, k in enumerate(keys):
            self.assertEqual(t.get(k), i)
        self.assertNotIn("dd", t)

    def test_classic_collision_pair(self):
        t = self.make()
        t.put("Aa", 1)
        t.put("BB", 2)
        self.assertEqual(t.get("Aa"), 1)
        self.assertEqual(t.get("BB"), 2)

    def test_grows_and_keeps_all(self):
        t = self.make(capacity=4, max_load=0.5)
        n = 1000
        for i in range(n):
            t.put(f"key{i}", i)
        self.assertEqual(len(t), n)
        self.assertLessEqual(t.load_factor(), 0.5)
        for i in range(n):
            self.assertEqual(t.get(f"key{i}"), i)
        self.assertNotIn("key1000", t)

    def test_no_resize_when_max_load_none(self):
        t = self.make(capacity=11, max_load=None)
        for i in range(5):
            t.put(str(i), i)
        self.assertEqual(t.capacity, 11)
        self.assertAlmostEqual(t.load_factor(), 5 / 11)

    def test_find_counts_comparisons(self):
        t = self.make(capacity=11, max_load=None)
        t.put("aj", 0)
        t.put("au", 1)
        found, value, cost = t.find("aj")
        self.assertTrue(found)
        self.assertEqual(value, 0)
        self.assertGreaterEqual(cost, 1)
        found2, _, cost2 = t.find("au")
        self.assertTrue(found2)
        self.assertGreater(cost2, cost)  # 뒤에 들어간 키는 더 많이 비교

    def test_non_string_key(self):
        t = self.make()
        for bad in (1, None, ("a",)):
            with self.assertRaises(TypeError):
                t.put(bad, 1)

    def test_bad_arguments(self):
        with self.assertRaises(ValueError):
            self.make(capacity=0)
        with self.assertRaises(ValueError):
            self.make(max_load=0)


class TestChainingHashTable(HashTableContract, unittest.TestCase):
    def make(self, **kw):
        return HashTable(**kw)

    def test_buckets_view(self):
        t = HashTable(capacity=11, max_load=None)
        t.put("aj", 1)
        t.put("au", 2)
        buckets = t.buckets()
        self.assertEqual(len(buckets), 11)
        self.assertEqual(buckets[0], [("aj", 1), ("au", 2)])  # 끝에 붙인다


class TestForbidden(unittest.TestCase):
    """src/ 에 dict, set, 내장 hash()가 없는지 구문 트리로 확인한다."""

    def test_src(self):
        banned_names = {"dict", "set", "frozenset", "hash"}  # 이 테스트 파일 안에서는 써도 된다
        for name in sorted(os.listdir(SRC)):
            if not name.endswith(".py"):
                continue
            with open(os.path.join(SRC, name), encoding="utf-8") as f:
                tree = ast.parse(f.read(), name)
            for node in ast.walk(tree):
                where = f"{name}:{getattr(node, 'lineno', '?')}"
                self.assertNotIsInstance(node, (ast.Dict, ast.Set, ast.DictComp, ast.SetComp), where)
                if isinstance(node, ast.Name):
                    self.assertNotIn(node.id, banned_names, where)
                if isinstance(node, ast.Attribute):
                    self.assertNotEqual(node.attr, "__dict__", where)


if __name__ == "__main__":
    unittest.main()
