# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/go-counting/canonical-data.json
# File last updated on 2023-07-19

import unittest

from go_counting import (
    Board,
    WHITE,
    BLACK,
    NONE,
)


class GoCountingTest(unittest.TestCase):
    def test_black_corner_territory_on_5x5_board(self):
        board = Board(["  B  ", " B B ", "B W B", " W W ", "  W  "])
        stone, territory = board.territory(x=0, y=1)
        self.assertEqual(stone, BLACK)
        self.assertSetEqual(territory, {(0, 0), (0, 1), (1, 0)})


if __name__ == "__main__":
    unittest.main()
