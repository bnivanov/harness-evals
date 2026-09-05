# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/pig-latin/canonical-data.json
# File last updated on 2023-07-19

import unittest

from pig_latin import (
    translate,
)


class PigLatinTest(unittest.TestCase):
    def test_word_beginning_with_a(self):
        self.assertEqual(translate("apple"), "appleay")


if __name__ == "__main__":
    unittest.main()
