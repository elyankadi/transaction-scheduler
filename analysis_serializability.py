import os
os.environ["PATH"] += os.pathsep + r"C:\Program Files (x86)\Graphviz\bin"
from typing import Dict, List, Set, Tuple
from model import Operation, OpType
from graphviz import Digraph

def _conflict(op1: Operation, op2: Operation) -> bool:
    """
    Conflict if:
      - different transactions
      - same item
      - and at least one is write-like (WRITE/INC/DEC)
    """
    if op1.tid == op2.tid: #since operations from the same transaction do not conflict as they are already ordered
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
    tids: Set[int] = {op.tid for op in history}
    graph: Dict[int, Set[int]] = {t: set() for t in tids}
    reasons: List[str] = []

    ops_by_item: Dict[str, List[Tuple[int, Operation]]] = {}
    for pos, op in enumerate(history):
        if op.item is None:
            continue
        if op.optype not in (OpType.READ, OpType.WRITE, OpType.INC, OpType.DEC):
            continue
        ops_by_item.setdefault(op.item, []).append((pos, op))

    for item, ops in ops_by_item.items():
        k = len(ops)
        for i in range(k):
            pos_i, oi = ops[i]
            for j in range(i + 1, k):
                pos_j, oj = ops[j]
                if _conflict(oi, oj):

                    # add edge once
                    graph[oi.tid].add(oj.tid)

                    # record every conflict reason
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

def visualize_precedence_graph(graph: Dict[int, Set[int]]) -> None:

    print("\n================ PRECEDENCE GRAPH ================")

    if not graph:
        print("Graph is empty.")
        return

    print("\nNodes:")
    for tid in sorted(graph.keys()):
        print(f"  T{tid}")

    print("\nEdges:")

    edge_found = False

    for tid in sorted(graph.keys()):
        for v in sorted(graph[tid]):
            print(f"  T{tid}  --->  T{v}")
            edge_found = True

    if not edge_found:
        print("  (no edges)")

    print("==================================================")

    # -------- GRAPHVIZ VISUALIZATION --------p

    dot = Digraph(comment="Precedence Graph")

    # add nodes
    for tid in graph:
        dot.node(f"T{tid}")

    # add edges
    for tid in graph:
        for v in graph[tid]:
            dot.edge(f"T{tid}", f"T{v}")

    # create graph image
    dot.render("precedence_graph", format="png", view=True)

def explain_serializability(is_cs: bool, graph, reasons, topo, cycle):
    print("\n=== Conflict Serializability Analysis ===")

    if reasons:
        print("\nEdges created because of conflicts:")
        max_show = 20
        for r in reasons[:max_show]:
            print(" -", r)
        if len(reasons) > max_show:
            print(f" - ... and {len(reasons) - max_show} more conflict(s).")

    if is_cs:
        print("\nAll conflicts were checked:")
        for r in reasons[:20]:
            print(" -", r)

        print("\nNo cycles detected → schedule is serializable.")
        print("\nSchedule is CONFLICT SERIALIZABLE.")

        all_orders = all_topological_sorts(graph)

        print("\nEquivalent serial order(s):")
        for order in all_orders:
            print(" → ".join(f"T{t}" for t in order))

        print(f"\nTotal equivalent serial schedules: {len(all_orders)}")

    else:
        print("\nSchedule is NOT conflict serializable.")

        if cycle:
            print("\n===== SERIALIZABILITY VIOLATION =====")
            print("Cycle detected in precedence graph:\n")

            cycle_str = " → ".join(f"T{t}" for t in cycle)
            print("    " + cycle_str)

            print("\nThis cycle means the schedule cannot be transformed")
            print("into any equivalent serial execution.")
            print("======================================")

def all_topological_sorts(graph: Dict[int, Set[int]]) -> List[List[int]]:
    """
    Generate ALL possible topological orders of the precedence graph.
    Used to list all equivalent serial schedules.
    """

    indeg = {u: 0 for u in graph}

    for u in graph:
        for v in graph[u]:
            indeg[v] += 1

    result = []
    visited = set()

    def backtrack(path, indeg):
        found = False

        for node in sorted(graph.keys()):
            if node not in visited and indeg[node] == 0:

                visited.add(node)
                path.append(node)

                new_indeg = indeg.copy()
                for v in graph[node]:
                    new_indeg[v] -= 1

                backtrack(path, new_indeg)

                visited.remove(node)
                path.pop()

                found = True

        if not found:
            result.append(path.copy())

    backtrack([], indeg)

    return result