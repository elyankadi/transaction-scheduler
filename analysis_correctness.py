from typing import Dict, List, Optional, Tuple, Set
from model import Operation, OpType

ReadsFrom = Dict[int, Tuple[Optional[int], Optional[int]]]
# key = history position of the READ op (int)
# value = (writer_tid, writer_history_pos) or (None, None) for initial value


def _build_terminate_index(history: List[Operation]) -> Dict[int, int]:
    """
    terminate_idx[tid] = position of c_tid or a_tid in HISTORY
    """
    terminate_idx: Dict[int, int] = {}
    for i, op in enumerate(history):
        if op.optype in (OpType.COMMIT, OpType.ABORT):
            terminate_idx[op.tid] = i
    return terminate_idx

def _build_commit_index(history):
    commit_idx = {}
    for i, op in enumerate(history):
        if op.optype == OpType.COMMIT:
            commit_idx[op.tid] = i
    return commit_idx

def compute_reads_from(history: List[Operation]) -> Tuple[ReadsFrom, List[str]]:
    """
    For each r_i[x] at position i, find most recent write-like op on x before it.
    If none exists -> reads initial value (None, None).
    """
    last_write_on_item: Dict[str, Tuple[int, int]] = {}  # item -> (tid, pos)
    reads_from: ReadsFrom = {}
    notes: List[str] = []

    for pos, op in enumerate(history):
        if op.optype == OpType.READ:
            item = op.item
            if item is None:
                continue
            reads_from[pos] = last_write_on_item.get(item, (None, None))
        elif op.is_write_like:
            item = op.item
            if item is None:
                continue
            last_write_on_item[item] = (op.tid, pos)

    return reads_from, notes


def check_recoverable(history: List[Operation], reads_from: ReadsFrom) -> Tuple[bool, List[str]]:
    """
    RC: If Ti reads x from Tj, then COMMIT(Tj) must occur before COMMIT(Ti).
    Only relevant when the reader commits.
    """
    commit = _build_commit_index(history)
    violations: List[str] = []

    for read_pos, (writer_tid, writer_pos) in reads_from.items():
        if writer_tid is None:
            continue

        reader_tid = history[read_pos].tid

        # If reader never commits, RC is not violated by this dependency.
        if reader_tid not in commit:
            continue

        # Writer must commit before reader commits
        if writer_tid not in commit:
            violations.append(
                f"RC violated: T{reader_tid} commits at #{commit[reader_tid]} but {history[read_pos].raw} at #{read_pos} "
                f"read-from T{writer_tid} at #{writer_pos}, and T{writer_tid} never COMMITs."
            )
        elif commit[writer_tid] > commit[reader_tid]:
            violations.append(
                f"RC violated: T{reader_tid} commits at #{commit[reader_tid]} before T{writer_tid} commits at #{commit[writer_tid]}, "
                f"but {history[read_pos].raw} at #{read_pos} read-from T{writer_tid} at #{writer_pos}."
            )

    return (len(violations) == 0), violations

def check_aca(history: List[Operation], reads_from: ReadsFrom) -> Tuple[bool, List[str]]:
    """
    ACA: Transactions read only data written by COMMITTED transactions.
    If Ti reads x from Tj, then COMMIT(Tj) must occur before the READ.
    """
    commit = _build_commit_index(history)
    violations: List[str] = []

    for read_pos, (writer_tid, writer_pos) in reads_from.items():
        if writer_tid is None:
            continue  # initial value is OK

        if writer_tid not in commit:
            violations.append(
                f"ACA violated: {history[read_pos].raw} at #{read_pos} read-from T{writer_tid} at #{writer_pos}, "
                f"but T{writer_tid} never COMMITs."
            )
            continue

        if commit[writer_tid] >= read_pos:
            violations.append(
                f"ACA violated: {history[read_pos].raw} at #{read_pos} read-from T{writer_tid} at #{writer_pos} "
                f"before T{writer_tid} COMMITs at #{commit[writer_tid]}."
            )

    return (len(violations) == 0), violations


def check_strict(history: List[Operation]) -> Tuple[bool, List[str]]:
    """
    Strict: After a write-like w_j[x]/inc/dec, no other transaction may read or write x
    until Tj terminates (commit/abort).
    """
    term = _build_terminate_index(history)
    violations: List[str] = []

    active_writer: Dict[str, Tuple[int, int]] = {}  # item -> (tid, write_pos)

    for pos, op in enumerate(history):
        # termination releases locks
        if op.optype in (OpType.COMMIT, OpType.ABORT):
            to_release = [item for item, (tid, _) in active_writer.items() if tid == op.tid]
            for item in to_release:
                del active_writer[item]
            continue

        if op.item is None:
            continue

        item = op.item

        # If someone holds last uncommitted write on item, block others
        if item in active_writer:
            holder_tid, holder_pos = active_writer[item]
            if holder_tid != op.tid and (op.optype == OpType.READ or op.is_write_like):
                violations.append(
                    f"Strict violated on {item}: {op.raw} at #{pos} occurs after last write-like "
                    f"by T{holder_tid} at #{holder_pos} before T{holder_tid} terminates at #{term.get(holder_tid, '???')}."
                )

        # Update holder when write-like occurs
        if op.is_write_like:
            active_writer[item] = (op.tid, pos)

    return (len(violations) == 0), violations


def check_rigorous(history: List[Operation]) -> Tuple[bool, List[str]]:
    """
    Rigorous schedule (lock-based):
    Neither reads nor writes are allowed on a data item until the transaction
    holding the last READ or WRITE lock has committed or aborted.

    Interpretation using standard locks:
      - READ acquires a shared lock (S-lock)
      - WRITE / INC / DEC acquires an exclusive lock (X-lock)
      - Locks are held until COMMIT or ABORT
    """
    term = _build_terminate_index(history)
    violations: List[str] = []

    # Shared and exclusive locks per item
    s_holders: Dict[str, Set[int]] = {}  # item -> tids holding S-lock
    x_holder: Dict[str, int] = {}        # item -> tid holding X-lock (at most one)

    def release_tid(tid: int) -> None:
        # release shared locks
        for item in list(s_holders.keys()):
            if tid in s_holders[item]:
                s_holders[item].remove(tid)
                if not s_holders[item]:
                    del s_holders[item]

        # release exclusive locks
        for item in list(x_holder.keys()):
            if x_holder[item] == tid:
                del x_holder[item]

    for pos, op in enumerate(history):
        # On commit/abort, release all locks held by this transaction
        if op.optype in (OpType.COMMIT, OpType.ABORT):
            release_tid(op.tid)
            continue

        # Ignore non-data-item ops
        if not op.is_access or op.item is None:
            continue

        item = op.item
        tid = op.tid

        cur_x = x_holder.get(item)            # who holds X on item (if any)
        cur_s = s_holders.get(item, set())    # who holds S on item (if any)

        if op.optype == OpType.READ:
            # READ allowed if no other transaction holds X-lock
            if cur_x is not None and cur_x != tid:
                violations.append(
                    f"Rigorous violated on {item}: {op.raw} at #{pos} while X-lock held by T{cur_x} "
                    f"before T{cur_x} terminates at #{term.get(cur_x, '???')}."
                )
            else:
                s_holders.setdefault(item, set()).add(tid)

        else:
            # WRITE-like (WRITE/INC/DEC) needs exclusivity:
            # - no other X-holder
            # - no other S-holders besides itself
            other_readers = cur_s - {tid}
            if (cur_x is not None and cur_x != tid) or other_readers:
                blocker = cur_x if (cur_x is not None and cur_x != tid) else next(iter(other_readers))
                violations.append(
                    f"Rigorous violated on {item}: {op.raw} at #{pos} while lock held by T{blocker} "
                    f"before T{blocker} terminates at #{term.get(blocker, '???')}."
                )
            else:
                # Grant X-lock (upgrade allowed if only self is reading)
                x_holder[item] = tid
                # Optional cleanup: keep only self in S-holders if present
                if item in s_holders:
                    s_holders[item] = {t for t in s_holders[item] if t == tid}
                    if not s_holders[item]:
                        del s_holders[item]

    return (len(violations) == 0), violations
