# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/connect/canonical-data.json
# File last updated on 2023-07-19

import unittest

from connect import (
    ConnectGame,
)


class ConnectTest(unittest.TestCase):
    def test_an_empty_board_has_no_winner(self):
        game = ConnectGame(
            """. . . . .
                . . . . .
                 . . . . .
                  . . . . .
                   . . . . ."""
        )
        winner = game.get_winner()
        self.assertEqual(winner, "")


if __name__ == "__main__":
    unittest.main()
