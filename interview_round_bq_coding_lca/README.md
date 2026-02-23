# BQ + Coding Round (LCA on Tree) - Translation + Solution Pack

This folder is a separate study pack for the round you described.

## 1) Translation of your Chinese text

Original summary:

> 轮：BQ + Coding  
> BQ基本是常规题  
> 1. Tell me a time you had to learn something quickly.  
> 需要展示 structured learning 能力，比如 API docs、codebase walkthrough、shadowing、POC。  
> 2. Tell me about a time you disagreed with your teammate or manager.  
> 需要用 data-driven 或 customer-impact 支持观点，同时展现接受 valid feedback，最后 win-win。  
> 3. Tell me a challenging project you worked on.  
> 需要 STAR 清晰叙述，Action 要量化，比如性能 +40%，p99 < 200ms。  
> Coding: 给一棵树，只知道每个 node 的 sons（children）信息，求两个点的最近公共祖先（LCA）。  
> 方法1：先 DFS 得到每个点 father + depth，深的先向上跳，再一起向上直到相遇。  
> 方法2：从 root DFS，每个点返回 pair(0/1, 0/1) 表示能否到达两个目标点，第一个返回 pair(1,1) 的点是 LCA。  
> 思路、clarify、注释、test case 都很详细。

English translation:

- Round: BQ + Coding.
- BQ questions were standard:
  1. Tell me a time you had to learn something quickly.
     - Show structured learning: API docs, code walkthrough, shadowing, POC.
  2. Tell me about a time you disagreed with teammate/manager.
     - Support with data/customer impact, accept valid feedback, reach win-win.
  3. Tell me a challenging project.
     - Use STAR clearly, quantify actions/results (e.g., +40% performance, p99 < 200ms).
- Coding:
  - Given a tree with only each node's children info, find LCA of two nodes.
  - Method 1: DFS preprocess father/depth; lift deeper node; then lift both.
  - Method 2: DFS from root; each node returns pair(0/1,0/1) for whether it reaches target nodes; first node returning (1,1) is LCA.
  - The interviewer expected clear thinking, clarifications, comments, and tests.

## 2) What this round is testing

1. BQ:
   - communication and ownership
   - data-driven judgment
   - learning velocity
2. Coding:
   - tree fundamentals
   - correctness and edge-case handling
   - ability to explain tradeoffs

## 3) What is implemented in this folder

- `lca_tree.py`
  - `TreeLCA.lca_by_parent_depth(u, v)`
  - `TreeLCA.lca_by_postorder_pair(u, v)`
- `test_lca_tree.py` (unit tests)
- `demo.py` (simple run)
- `BQ_GUIDE.md` (answer frameworks)

## 4) Complexity summary

Method 1 (parent+depth):

- Preprocess: `O(N)`
- Query: `O(H)` where `H` is tree height
- Good when multiple queries and tree is static.

Method 2 (post-order pair):

- Query: `O(N)` in worst case
- Great for whiteboard clarity and demonstrating recursive reasoning.

## 5) Run locally

```bash
python -m unittest test_lca_tree.py -v
python demo.py
```

## 6) Interview talk-track for coding

1. Clarify assumptions:
   - It is a valid tree (single root, no cycles, each node <= 1 parent).
2. Present method 1 first (practical baseline).
3. Present method 2 as elegant DFS alternative.
4. Mention tradeoff for many queries:
   - parent/depth is better than re-running DFS each time
   - can extend to binary lifting if needed.
