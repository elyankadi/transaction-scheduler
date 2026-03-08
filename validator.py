from typing import Dict, List, Set, Tuple
from model import Operation, OpType

class ValidationError(Exception):
    pass

def validate_transaction_ops(tid: int, ops: List[Operation]) -> List[Operation]:
    """
    Validates and possibly fixes transaction definition.

    Rules:
    - If START missing, auto-insert it.
    - Transaction must end with exactly one COMMIT or ABORT.
    - No COMMIT/ABORT allowed in the middle.
    - No additional START allowed after position 0.
    """

    if not ops:
        raise ValidationError(f"T{tid}: empty transaction.")

    # -------- Auto insert START if missing --------
    if ops[0].optype != OpType.START:
        ops = [Operation(OpType.START, tid, None, f"s{tid}")] + ops

    # -------- Ensure only one START at position 0 --------
    for i, op in enumerate(ops):
        if op.optype == OpType.START and i != 0:
            raise ValidationError(
                f"T{tid}: START operation can only appear at the beginning."
            )

    # -------- Ensure all ops belong to same transaction --------
    for op in ops:
        if op.tid != tid:
            raise ValidationError(
                f"T{tid}: contains operation from different transaction: {op.raw}"
            )

    # -------- Check commit/abort rules --------
    end_ops = [op for op in ops if op.optype in (OpType.COMMIT, OpType.ABORT)]

    if len(end_ops) == 0:
        raise ValidationError(
            f"T{tid}: must end with COMMIT or ABORT."
        )

    if len(end_ops) > 1:
        raise ValidationError(
            f"T{tid}: multiple COMMIT/ABORT operations detected."
        )

    if ops[-1].optype not in (OpType.COMMIT, OpType.ABORT):
        raise ValidationError(
            f"T{tid}: COMMIT/ABORT must be the LAST operation."
        )

    # -------- No commit/abort allowed in middle --------
    for i, op in enumerate(ops[:-1]):
        if op.optype in (OpType.COMMIT, OpType.ABORT):
            raise ValidationError(
                f"T{tid}: COMMIT/ABORT appears before the end."
            )

    return ops

def validate_history_against_transactions(
    history: List[Operation],
    tx_ops: Dict[int, List[Operation]]
) -> None:

    known = set(tx_ops.keys())

    for op in history:
        if op.tid not in known:
            raise ValidationError(
                f"History contains operation for unknown transaction T{op.tid}: {op.raw}"
            )

    pointers = {tid: 0 for tid in tx_ops}

    for op in history:
        tid = op.tid
        expected_ops = tx_ops[tid]
        p = pointers[tid]

        if p >= len(expected_ops):
            raise ValidationError(
                f"History contains too many operations for T{tid}."
            )

        expected = expected_ops[p]

        if (
            op.optype != expected.optype
            or op.item != expected.item
            or op.tid != expected.tid
        ):
            raise ValidationError(
                f"History order mismatch for T{tid}: got {op.raw}, expected {expected.raw}"
            )

        pointers[tid] += 1

    # Ensure all transactions completed
    for tid, p in pointers.items():
        if p != len(tx_ops[tid]):
            remaining = [op.raw for op in tx_ops[tid][p:]]
            raise ValidationError(
                f"History ended early. Missing operations for T{tid}: {remaining}"
            )