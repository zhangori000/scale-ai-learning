from __future__ import annotations

from lca_tree import TreeLCA


def main() -> None:
    children = {
        "A": ["B", "C"],
        "B": ["D", "E"],
        "C": ["F"],
        "F": ["G"],
    }

    lca = TreeLCA(children)

    queries = [
        ("D", "E"),
        ("D", "G"),
        ("F", "G"),
        ("B", "G"),
        ("C", "C"),
    ]

    for u, v in queries:
        m1 = lca.lca_by_parent_depth(u, v)
        m2 = lca.lca_by_postorder_pair(u, v).node
        print(f"query({u}, {v}) -> parent_depth={m1}, postorder_pair={m2}")


if __name__ == "__main__":
    main()
