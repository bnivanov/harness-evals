import unittest

from simple_linked_list import LinkedList, EmptyListException


# No canonical data available for this exercise

class SimpleLinkedListTest(unittest.TestCase):
    def test_empty_list_has_len_zero(self):
        sut = LinkedList()
        self.assertEqual(len(sut), 0)


if __name__ == "__main__":
    unittest.main()
