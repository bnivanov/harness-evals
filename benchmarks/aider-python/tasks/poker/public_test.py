# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/poker/canonical-data.json
# File last updated on 2023-12-27

import unittest

from poker import (
    best_hands,
)


class PokerTest(unittest.TestCase):
    def test_single_hand_always_wins(self):
        self.assertEqual(best_hands(["4S 5S 7H 8D JC"]), ["4S 5S 7H 8D JC"])


if __name__ == "__main__":
    unittest.main()
