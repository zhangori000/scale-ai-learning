from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Hashable


Node = Hashable


@dataclass(frozen=True)
class LCAResult:
    node: Node | None
    found_u: bool
    found_v: bool


class TreeLCA:
    """
    LCA helper for an N-ary tree when input is "node -> children list".

    Supports:
    1) Parent+depth lifting (good baseline, O(H) per query)
    2) Post-order DFS pair-return method (the pair(0/1, 0/1) idea)
    """

    def __init__(self, children: dict[Node, list[Node]], root: Node | None = None) -> None:
        if not children:
            raise ValueError("children map cannot be empty")

        self.children = self._normalize_children(children)
        self.root = self._resolve_root(self.children, root)

        self.parent: dict[Node, Node | None] = {}
        self.depth: dict[Node, int] = {}
        self._build_parent_depth()

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------
    def lca_by_parent_depth(self, u: Node, v: Node) -> Node | None:
        """
        Method 1 from interview prompt:
        - preprocess parent/depth
        - lift deeper node up
        - move both up until they meet
        """
        self._assert_node_exists(u)
        self._assert_node_exists(v)

        if u == v:
            return u

        a, b = u, v
        da, db = self.depth[a], self.depth[b]

        # Lift deeper node.
        while da > db:
            a = self.parent[a]  # type: ignore[assignment]
            da -= 1
        while db > da:
            b = self.parent[b]  # type: ignore[assignment]
            db -= 1

        # Move both upward until meeting point.
        while a != b:
            pa = self.parent[a]
            pb = self.parent[b]
            if pa is None or pb is None:
                return None
            a, b = pa, pb
        return a

    def lca_by_postorder_pair(self, u: Node, v: Node) -> LCAResult:
        """
        Method 2 from interview prompt:
        Post-order DFS where each node returns pair:
        (can_reach_u:0/1, can_reach_v:0/1)
        The first node in post-order that becomes (1,1) is the LCA.
        """
        self._assert_node_exists(u)
        self._assert_node_exists(v)
        return self._dfs_pair(self.root, u, v)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_children(children: dict[Node, list[Node]]) -> dict[Node, list[Node]]:
        normalized: dict[Node, list[Node]] = {k: list(v) for k, v in children.items()}
        # Ensure leaves that only appear as child still exist as keys.
        for child_list in list(normalized.values()):
            for child in child_list:
                normalized.setdefault(child, [])
        return normalized

    @staticmethod
    def _resolve_root(children: dict[Node, list[Node]], root: Node | None) -> Node:
        parent_count: dict[Node, int] = {node: 0 for node in children}
        for node, kids in children.items():
            for child in kids:
                parent_count[child] = parent_count.get(child, 0) + 1
                if parent_count[child] > 1:
                    raise ValueError(
                        f"invalid tree: node {child!r} has multiple parents"
                    )

        roots = [node for node, count in parent_count.items() if count == 0]
        if root is not None:
            if root not in children:
                raise ValueError(f"provided root {root!r} not in tree")
            return root
        if len(roots) != 1:
            raise ValueError(
                f"cannot infer unique root; candidates={roots}"
            )
        return roots[0]

    def _build_parent_depth(self) -> None:
        self.parent[self.root] = None
        self.depth[self.root] = 0

        visited: set[Node] = set()
        q: deque[Node] = deque([self.root])

        while q:
            node = q.popleft()
            if node in visited:
                raise ValueError("invalid tree: cycle detected")
            visited.add(node)

            for child in self.children[node]:
                if child in self.parent:
                    # Multiple paths to same node is not a tree.
                    if self.parent[child] != node:
                        raise ValueError(
                            f"invalid tree: node {child!r} reachable from multiple parents"
                        )
                self.parent[child] = node
                self.depth[child] = self.depth[node] + 1
                q.append(child)

        if len(visited) != len(self.children):
            unreachable = set(self.children) - visited
            raise ValueError(f"invalid tree: disconnected nodes found {unreachable}")

    def _dfs_pair(self, node: Node, u: Node, v: Node) -> LCAResult:
        found_u = node == u
        found_v = node == v

        # Post-order traversal:
        # if any child already found LCA, bubble it up unchanged.
        for child in self.children[node]:
            child_res = self._dfs_pair(child, u, v)
            if child_res.node is not None:
                return child_res
            found_u = found_u or child_res.found_u
            found_v = found_v or child_res.found_v

        # First node in post-order with both flags true is LCA.
        if found_u and found_v:
            return LCAResult(node=node, found_u=True, found_v=True)
        return LCAResult(node=None, found_u=found_u, found_v=found_v)

    def _assert_node_exists(self, node: Node) -> None:
        if node not in self.children:
            raise KeyError(f"node not found: {node!r}")


__all__ = ["TreeLCA", "LCAResult"]
