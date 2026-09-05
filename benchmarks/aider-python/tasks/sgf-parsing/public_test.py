# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/sgf-parsing/canonical-data.json
# File last updated on 2023-07-19

import unittest

from sgf_parsing import (
    parse,
    SgfTree,
)


class SgfParsingTest(unittest.TestCase):
    def test_empty_input(self):
        input_string = ""
        with self.assertRaises(ValueError) as err:
            parse(input_string)
        self.assertEqual(type(err.exception), ValueError)
        self.assertEqual(err.exception.args[0], "tree missing")


if __name__ == "__main__":
    unittest.main()
