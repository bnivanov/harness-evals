import unittest

import hangman
from hangman import Hangman


# Tests adapted from csharp//hangman/HangmanTest.cs

class HangmanTests(unittest.TestCase):
    def test_initially_9_failures_are_allowed(self):
        game = Hangman('foo')
        self.assertEqual(game.get_status(), hangman.STATUS_ONGOING)
        self.assertEqual(game.remaining_guesses, 9)


if __name__ == "__main__":
    unittest.main()
