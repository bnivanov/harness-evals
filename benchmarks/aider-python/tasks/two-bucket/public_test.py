# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/two-bucket/canonical-data.json
# File last updated on 2023-07-21

import unittest

from two_bucket import (
    measure,
)


class TwoBucketTest(unittest.TestCase):
    def test_measure_using_bucket_one_of_size_3_and_bucket_two_of_size_5_start_with_bucket_one(
        self,
    ):
        self.assertEqual(measure(3, 5, 1, "one"), (4, "one", 5))


if __name__ == "__main__":
    unittest.main()
