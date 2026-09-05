import unittest

from tree_building import Record, BuildTree


class TreeBuildingTest(unittest.TestCase):
    """
        Record(record_id, parent_id): records given to be processed
        Node(node_id): Node in tree
        BuildTree(records): records as argument and returns tree
        BuildTree should raise ValueError if given records are invalid
    """

    def test_empty_list_input(self):
        records = []
        root = BuildTree(records)
        self.assertIsNone(root)


if __name__ == "__main__":
    unittest.main()
