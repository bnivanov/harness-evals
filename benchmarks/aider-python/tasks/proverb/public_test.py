# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/proverb/canonical-data.json
# File last updated on 2023-07-19

import unittest

from proverb import (
    proverb,
)

# PLEASE TAKE NOTE: Expected result lists for these test cases use **implicit line joining.**
# A new line in a result list below **does not** always equal a new list element.
# Check comma placement carefully!


class ProverbTest(unittest.TestCase):
    def test_zero_pieces(self):
        input_data = []
        self.assertEqual(proverb(*input_data, qualifier=None), [])


if __name__ == "__main__":
    unittest.main()
