# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/pov/canonical-data.json
# File last updated on 2023-07-19

import unittest

from pov import (
    Tree,
)


class PovTest(unittest.TestCase):
    def test_results_in_the_same_tree_if_the_input_tree_is_a_singleton(self):
        tree = Tree("x")
        expected = Tree("x")
        self.assertTreeEquals(tree.from_pov("x"), expected)


if __name__ == "__main__":
    unittest.main()
