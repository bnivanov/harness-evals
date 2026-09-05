# These tests are auto-generated with test data from:
# https://github.com/exercism/problem-specifications/tree/main/exercises/book-store/canonical-data.json
# File last updated on 2023-07-20

import unittest

from book_store import (
    total,
)


class BookStoreTest(unittest.TestCase):
    def test_only_a_single_book(self):
        basket = [1]
        self.assertEqual(total(basket), 800)


if __name__ == "__main__":
    unittest.main()
