from __future__ import annotations

import unittest

from lca_tree import TreeLCA


class TreeLCATest(unittest.TestCase):
    def setUp(self) -> None:
        # Tree:
        #         1
        #       /   \
        #      2     3
        #    /  \     \
        #   4    5     6
        #               \
        #                7
        self.children = {
            1: [2, 3],
            2: [4, 5],
            3: [6],
            6: [7],
        }
        self.lca = TreeLCA(self.children)

    def test_lca_by_parent_depth(self) -> None:
        self.assertEqual(self.lca.lca_by_parent_depth(4, 5), 2)
        self.assertEqual(self.lca.lca_by_parent_depth(4, 7), 1)
        self.assertEqual(self.lca.lca_by_parent_depth(6, 7), 6)
        self.assertEqual(self.lca.lca_by_parent_depth(2, 7), 1)
        self.assertEqual(self.lca.lca_by_parent_depth(3, 3), 3)

    def test_lca_by_postorder_pair(self) -> None:
        self.assertEqual(self.lca.lca_by_postorder_pair(4, 5).node, 2)
        self.assertEqual(self.lca.lca_by_postorder_pair(4, 7).node, 1)
        self.assertEqual(self.lca.lca_by_postorder_pair(6, 7).node, 6)
        self.assertEqual(self.lca.lca_by_postorder_pair(2, 7).node, 1)
        self.assertEqual(self.lca.lca_by_postorder_pair(3, 3).node, 3)

    def test_methods_agree(self) -> None:
        pairs = [(4, 5), (4, 7), (6, 7), (2, 7), (3, 3)]
        for u, v in pairs:
            m1 = self.lca.lca_by_parent_depth(u, v)
            m2 = self.lca.lca_by_postorder_pair(u, v).node
            self.assertEqual(m1, m2)

    def test_missing_node(self) -> None:
        with self.assertRaises(KeyError):
            self.lca.lca_by_parent_depth(4, 999)
        with self.assertRaises(KeyError):
            self.lca.lca_by_postorder_pair(4, 999)

    def test_invalid_multiple_parents(self) -> None:
        bad = {
            1: [2, 3],
            3: [2],  # node 2 has multiple parents
        }
        with self.assertRaises(ValueError):
            TreeLCA(bad)

    def test_invalid_disconnected(self) -> None:
        disconnected = {
            1: [2],
            3: [],  # disconnected component
        }
        with self.assertRaises(ValueError):
            TreeLCA(disconnected)


if __name__ == "__main__":
    unittest.main()
