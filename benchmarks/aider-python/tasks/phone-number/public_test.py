# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/phone-number/canonical-data.json
# File last updated on 2023-07-19

import unittest

from phone_number import (
    PhoneNumber,
)


class PhoneNumberTest(unittest.TestCase):
    def test_cleans_the_number(self):
        number = PhoneNumber("(223) 456-7890").number
        self.assertEqual(number, "2234567890")


if __name__ == "__main__":
    unittest.main()
