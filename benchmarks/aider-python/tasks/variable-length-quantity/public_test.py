# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/variable-length-quantity/canonical-data.json
# File last updated on 2023-07-19

import unittest

from variable_length_quantity import (
    decode,
    encode,
)


class VariableLengthQuantityTest(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(encode([0x0]), [0x0])


if __name__ == "__main__":
    unittest.main()
