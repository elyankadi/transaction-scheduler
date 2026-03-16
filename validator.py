from typing import Dict, List, Tuple
from collections import Counter
from model import Operation, OpType


class ValidationError(Exception):
    pass


def _op_signature(op: Operation) -> Tuple:
    """
    Normalized signature used to compare operations independent of raw notation.
    """
    return (op.optype, op.tid, op.item)


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
        raise ValidationError(f"T{tid}: must end with COMMIT or ABORT.")

    if len(end_ops) > 1:
        raise ValidationError(f"T{tid}: multiple COMMIT/ABORT operations detected.")

    if ops[-1].optype not in (OpType.COMMIT, OpType.ABORT):
        raise ValidationError(f"T{tid}: COMMIT/ABORT must be the LAST operation.")

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
) -> List[str]:
    """
    Validates that HISTORY uses only known transactions and contains exactly
    the same operations as the registered transactions.

    IMPORTANT:
    - If intra-transaction order is violated, this is only a WARNING.
    - Fatal errors are raised only for:
        * unknown transaction ids
        * missing operations
        * extra operations
        * wrong operations not belonging to the transaction definition
    Returns:
        warnings: list of warning strings
    """

    warnings: List[str] = []
    known = set(tx_ops.keys())

    # -------- Unknown transaction check --------
    for op in history:
        if op.tid not in known:
            raise ValidationError(
                f"History contains operation for unknown transaction T{op.tid}: {op.raw}"
            )

    # -------- Group actual history ops by transaction --------
    actual_by_tid: Dict[int, List[Operation]] = {tid: [] for tid in tx_ops}
    for op in history:
        actual_by_tid[op.tid].append(op)

    # -------- Compare each transaction separately --------
    for tid, expected_ops in tx_ops.items():
        actual_ops = actual_by_tid[tid]

        # 1) Length must match exactly
                # 1) Length mismatch (allow ACTIVE transactions)
        if len(actual_ops) != len(expected_ops):

            # Case: transaction not finished in history
            if len(actual_ops) < len(expected_ops):

                missing_ops = expected_ops[len(actual_ops):]

                # Check if transaction has already terminated
                if not any(op.optype in (OpType.COMMIT, OpType.ABORT) for op in actual_ops):

                    warnings.append(
                        f"Transaction T{tid} is ACTIVE in the history "
                        f"(no COMMIT/ABORT encountered). "
                        f"Missing operations: {[op.raw for op in missing_ops]}"
                    )

                else:

                    warnings.append(
                        f"Transaction T{tid} did not finish in the history. "
                        f"Missing operations: {[op.raw for op in missing_ops]}"
                    )

                # Continue analysis
                continue

            # Case: extra operations (still invalid)
            else:
                extras = [op.raw for op in actual_ops[len(expected_ops):]]
                raise ValidationError(
                    f"History contains too many operations for T{tid}. "
                    f"Expected {len(expected_ops)} operations but found {len(actual_ops)}. "
                    f"Extra operation(s): {extras}"
                )

        # 2) Same multiset of operations must appear
        expected_counter = Counter(_op_signature(op) for op in expected_ops)
        actual_counter = Counter(_op_signature(op) for op in actual_ops)

        if expected_counter != actual_counter:
            raise ValidationError(
                f"History operations for T{tid} do not match the registered transaction definition.\n"
                f"Expected: {' '.join(op.raw for op in expected_ops)}\n"
                f"Found:    {' '.join(op.raw for op in actual_ops)}"
            )

        # 3) Order mismatch becomes WARNING only
        expected_sig = [_op_signature(op) for op in expected_ops]
        actual_sig = [_op_signature(op) for op in actual_ops]

        if actual_sig != expected_sig:
            warnings.append(
                f"T{tid}: operation order inside the transaction is violated.\n"
                f"   Expected order: {' '.join(op.raw for op in expected_ops)}\n"
                f"   Found in history: {' '.join(op.raw for op in actual_ops)}\n"
                f"   Analysis will continue, but this schedule is unrealistic from a DBMS execution perspective."
            )

            # Optional: show pairwise mismatches
            for i, (act, exp) in enumerate(zip(actual_ops, expected_ops), start=1):
                if _op_signature(act) != _op_signature(exp):
                    warnings.append(
                        f"   First mismatch around position {i} within T{tid}: "
                        f"got {act.raw}, expected {exp.raw}"
                    )
                    break

    return warnings