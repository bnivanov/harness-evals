# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/affine-cipher/canonical-data.json
# File last updated on 2023-07-20

import unittest

from affine_cipher import (
    decode,
    encode,
)


class AffineCipherTest(unittest.TestCase):
    def test_encode_yes(self):
        self.assertEqual(encode("yes", 5, 7), "xbt")


if __name__ == "__main__":
    unittest.main()
