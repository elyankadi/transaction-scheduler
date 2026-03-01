from typing import Dict, List, Tuple
from model import Operation, OpType

class ValidationError(Exception):
    pass

def validate_transaction_ops(tid: int, ops: List[Operation]) -> List[Operation]:
    """
    Validates and possibly fixes transaction definition.
    - If START missing, auto-insert.
    - Must end with exactly one COMMIT or ABORT.
    - No commit/abort allowed in middle.
    Returns possibly updated ops list.
    """

    if not ops:
        raise ValidationError(f"T{tid}: empty transaction.")

    # Auto insert START if missing
    # START must be the first operation (strict requirement)
    if ops[0].optype != OpType.START:
        raise ValidationError(
            f"T{tid}: must begin with START(T{tid}) as the first operation."
        )

    # Check commit/abort rules
    end_ops = [op for op in ops if op.optype in (OpType.COMMIT, OpType.ABORT)]

    if len(end_ops) == 0:
        raise ValidationError(f"T{tid}: must end with c{tid} or a{tid} (COMMIT/ABORT missing).")

    if len(end_ops) > 1:
        raise ValidationError(f"T{tid}: multiple COMMIT/ABORT operations detected.")

    if ops[-1].optype not in (OpType.COMMIT, OpType.ABORT):
        raise ValidationError(f"T{tid}: COMMIT/ABORT must be the LAST operation.")

    # No commit/abort in middle
    for i, op in enumerate(ops[:-1]):
        if op.optype in (OpType.COMMIT, OpType.ABORT):
            raise ValidationError(
                f"T{tid}: COMMIT/ABORT found at position {i}, but must only appear at the end."
            )
    # Allowed operation types according to project requirements
    allowed_types = {
        OpType.START,
        OpType.READ,
        OpType.WRITE,
        OpType.INC,
        OpType.DEC,
        OpType.COMMIT,
        OpType.ABORT,
    }

    # Ensure only valid operations exist
    for i, op in enumerate(ops):
        if op.optype not in allowed_types:
            raise ValidationError(
                f"T{tid}: invalid operation type '{op.optype}' found in {op.raw}. "
                f"Only START, READ, WRITE, INC, DEC, COMMIT, ABORT are allowed."
        )
    # Ensure all ops belong to this transaction
    for op in ops:
        if op.tid != tid:
            raise ValidationError(f"T{tid}: contains operation from different transaction: {op.raw}")

    return ops

def validate_history_against_transactions(
    history: List[Operation],
    tx_ops: Dict[int, List[Operation]]
) -> None:
    # 1) only known tids
    known = set(tx_ops.keys())
    for op in history:
        if op.tid not in known:
            raise ValidationError(f"History contains op for unknown transaction T{op.tid}: {op.raw}")

    # 2) history must preserve each transaction's internal order
    # build expected sequences per transaction (by raw tokens)
    expected = {tid: [op.raw for op in ops] for tid, ops in tx_ops.items()}
    pointers = {tid: 0 for tid in tx_ops}

    for op in history:
        tid = op.tid
        seq = expected[tid]
        p = pointers[tid]
        if p >= len(seq) or op.raw != seq[p]:
            wanted = seq[p] if p < len(seq) else "(no more ops expected)"
            raise ValidationError(
                f"History order mismatch for T{tid}: got {op.raw}, expected {wanted}"
            )
        pointers[tid] += 1

    # 3) all transactions must appear fully in history (optional but recommended)
    for tid, p in pointers.items():
        if p != len(expected[tid]):
            remaining = expected[tid][p:]
            raise ValidationError(f"History ended early: missing ops for T{tid}: {remaining}")