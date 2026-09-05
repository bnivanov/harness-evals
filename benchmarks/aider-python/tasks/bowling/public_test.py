# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/bowling/canonical-data.json
# File last updated on 2023-07-21

import unittest

from bowling import (
    BowlingGame,
)


class BowlingTest(unittest.TestCase):
    def roll_new_game(self, rolls):
        game = BowlingGame()
        for roll in rolls:
            game.roll(roll)
        return game

    def test_should_be_able_to_score_a_game_with_all_zeros(self):
        rolls = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        game = self.roll_new_game(rolls)
        self.assertEqual(game.score(), 0)


if __name__ == "__main__":
    unittest.main()
