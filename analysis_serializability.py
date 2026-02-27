from typing import Dict, List, Set, Tuple
from model import Operation, OpType


def _conflict(op1: Operation, op2: Operation) -> bool:
    """
    Conflict if:
      - different transactions
      - same item
      - and at least one is write-like (WRITE/INC/DEC)
    """
    if op1.tid == op2.tid:
        return False
    if op1.item is None or op2.item is None:
        return False
    if op1.item != op2.item:
        return False

    # READ-READ never conflicts
    if op1.optype == OpType.READ and op2.optype == OpType.READ:
        return False

    return op1.is_write_like or op2.is_write_like


def build_precedence_graph(history: List[Operation]) -> Tuple[Dict[int, Set[int]], List[str]]:
    """
    Build precedence graph (conflict graph):
      Edge Ti -> Tj if there exist conflicting operations oi in Ti and oj in Tj
      such that oi appears before oj in the history.
    Returns:
      graph: adjacency list {tid: set(of tids)}
      reasons: human-readable edge reasons
    """
    # collect tids
    tids: Set[int] = {op.tid for op in history}
    graph: Dict[int, Set[int]] = {t: set() for t in tids}
    reasons: List[str] = []

    # For efficiency, group operations by item and only compare within same item.
    ops_by_item: Dict[str, List[Tuple[int, Operation]]] = {}
    for pos, op in enumerate(history):
        if op.item is None:
            continue
        if op.optype not in (OpType.READ, OpType.WRITE, OpType.INC, OpType.DEC):
            continue
        ops_by_item.setdefault(op.item, []).append((pos, op))

    # For each item, compare earlier vs later operations (worst-case O(k^2) per item),
    # but item grouping avoids comparing unrelated operations.
    for item, ops in ops_by_item.items():
        k = len(ops)
        for i in range(k):
            pos_i, oi = ops[i]
            for j in range(i + 1, k):
                pos_j, oj = ops[j]
                if _conflict(oi, oj):
                    if oj.tid not in graph[oi.tid]:
                        graph[oi.tid].add(oj.tid)
                        reasons.append(
                            f"Edge T{oi.tid} -> T{oj.tid} because {oi.raw} at #{pos_i} conflicts with {oj.raw} at #{pos_j} on item {item}."
                        )

    return graph, reasons


def _dfs_cycle(graph: Dict[int, Set[int]]) -> Tuple[bool, List[int]]:
    """
    Cycle detection with DFS.
    Returns (has_cycle, cycle_path).
    cycle_path is a list of tids in the cycle (approximate path).
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[int, int] = {u: WHITE for u in graph}
    parent: Dict[int, int] = {}

    def dfs(u: int) -> Tuple[bool, List[int]]:
        color[u] = GRAY
        for v in graph[u]:
            if color[v] == WHITE:
                parent[v] = u
                found, cyc = dfs(v)
                if found:
                    return True, cyc
            elif color[v] == GRAY:
                # back-edge found -> cycle
                # reconstruct cycle u -> ... -> v
                cycle = [v]
                cur = u
                while cur != v and cur in parent:
                    cycle.append(cur)
                    cur = parent[cur]
                cycle.append(v)
                cycle.reverse()
                return True, cycle
        color[u] = BLACK
        return False, []

    for node in graph:
        if color[node] == WHITE:
            found, cyc = dfs(node)
            if found:
                return True, cyc
    return False, []


def topological_sort(graph: Dict[int, Set[int]]) -> Tuple[bool, List[int]]:
    """
    Kahn's algorithm for topological ordering.
    Returns (ok, order). ok=False if cycle exists.
    """
    indeg: Dict[int, int] = {u: 0 for u in graph}
    for u in graph:
        for v in graph[u]:
            indeg[v] += 1

    queue = [u for u in indeg if indeg[u] == 0]
    order: List[int] = []

    while queue:
        u = queue.pop(0)
        order.append(u)
        for v in graph[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)

    if len(order) != len(graph):
        return False, []
    return True, order


def check_conflict_serializable(history: List[Operation]) -> Tuple[bool, Dict[int, Set[int]], List[str], List[int], List[int]]:
    """
    Returns:
      is_cs: conflict-serializable?
      graph
      reasons (edges explanations)
      topo_order (if serializable)
      cycle_path (if not serializable)
    """
    graph, reasons = build_precedence_graph(history)
    has_cycle, cycle_path = _dfs_cycle(graph)

    if has_cycle:
        return False, graph, reasons, [], cycle_path

    ok, topo = topological_sort(graph)
    if not ok:
        # should not happen if DFS found no cycle, but keep safe
        return False, graph, reasons, [], []
    return True, graph, reasons, topo, []