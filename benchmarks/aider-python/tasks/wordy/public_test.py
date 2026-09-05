# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/wordy/canonical-data.json
# File last updated on 2023-07-19

import unittest

from wordy import (
    answer,
)


class WordyTest(unittest.TestCase):
    def test_just_a_number(self):
        self.assertEqual(answer("What is 5?"), 5)


if __name__ == "__main__":
    unittest.main()
