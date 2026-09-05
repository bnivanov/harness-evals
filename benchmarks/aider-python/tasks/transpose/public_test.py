# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/transpose/canonical-data.json
# File last updated on 2024-08-26

import unittest

from transpose import (
    transpose,
)


class TransposeTest(unittest.TestCase):
    def test_empty_string(self):
        text = ""
        expected = ""

        self.assertEqual(transpose(text), expected)


if __name__ == "__main__":
    unittest.main()
