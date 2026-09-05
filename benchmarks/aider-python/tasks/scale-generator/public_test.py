# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/scale-generator/canonical-data.json
# File last updated on 2023-07-19

import unittest

from scale_generator import (
    Scale,
)


class ScaleGeneratorTest(unittest.TestCase):

    # Test chromatic scales
    def test_chromatic_scale_with_sharps(self):
        expected = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        self.assertEqual(Scale("C").chromatic(), expected)


if __name__ == "__main__":
    unittest.main()
