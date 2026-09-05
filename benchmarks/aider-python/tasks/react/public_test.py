# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/react/canonical-data.json
# File last updated on 2023-07-19

from functools import partial
import unittest

from react import (
    InputCell,
    ComputeCell,
)


class ReactTest(unittest.TestCase):
    def test_input_cells_have_a_value(self):
        input = InputCell(10)
        self.assertEqual(input.value, 10)


if __name__ == "__main__":
    unittest.main()
