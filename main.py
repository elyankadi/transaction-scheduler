from parser import parse_ops
from validator import (
    validate_transaction_ops,
    validate_history_against_transactions,
    ValidationError,
)
from analysis_correctness import (
    compute_reads_from,
    check_recoverable,
    check_aca,
    check_strict,
    check_rigorous,
)
from analysis_serializability import check_conflict_serializable


def main():
    print("=== Transaction Scheduling & Correctness Analyzer ===")
    n = int(input("Enter number of transactions: ").strip())

    tx_ops = {} # tid -> list of operations to be stored for validation of histories

    print("\nEnter each transaction.")
    print("You may omit START (it will be auto-added).")
    print("Example T1: w1[x] r1[y] c1")
    print("Example T2: s2 r2[x] inc2[x] c2\n")

    # ---------------- TRANSACTION INPUT ----------------
    for tid in range(1, n + 1):
        s = input(f"Enter T{tid}: ").strip()
        ops = parse_ops(s)

        try:
            ops = validate_transaction_ops(tid, ops)
        except ValidationError as e:
            print("\n Transaction definition invalid:")
            print(" -", e)
            return

        tx_ops[tid] = ops

    print("\nTransactions registered successfully.")
    print("Now you may test multiple histories.")
    print("Type 'exit' to stop.\n")

    # ---------------- HISTORY LOOP ----------------
    while True:
        hist_str = input("Enter HISTORY (or 'exit'): ").strip()

        if hist_str.lower() == "exit":
            print("Exiting program.")
            break

        try:
            history = parse_ops(hist_str)
            validate_history_against_transactions(history, tx_ops)
        except Exception as e:
            print("\n Invalid history:")
            print(" -", e)
            print()
            continue

        print("\n History accepted. Running checks...\n")

        # ---------- Correctness ----------
        reads_from, _ = compute_reads_from(history)

        rc_ok, rc_v = check_recoverable(history, reads_from)
        aca_ok, aca_v = check_aca(history, reads_from)
        strict_ok, strict_v = check_strict(history)
        rig_ok, rig_v = check_rigorous(history)

        print("=== Correctness Properties ===")

        print("\nRecoverable (RC):", "YES" if rc_ok else "NO")
        for v in rc_v:
            print(" -", v)

        print("\nACA:", "YES" if aca_ok else "NO")
        for v in aca_v:
            print(" -", v)

        print("\nStrict:", "YES" if strict_ok else "NO")
        for v in strict_v:
            print(" -", v)

        print("\nRigorous:", "YES" if rig_ok else "NO")
        for v in rig_v:
            print(" -", v)

        # ---------- Conflict Serializability ----------
        cs_ok, graph, edge_reasons, serial_order, cycle_path = check_conflict_serializable(history)

        print("\n=== Conflict Serializability ===")
        print("Conflict-Serializable:", "YES" if cs_ok else "NO")

        if edge_reasons:
            print("\nPrecedence Graph Edges:")
            for r in edge_reasons:
                print(" -", r)
        else:
            print("\nPrecedence Graph Edges: (none)")

        if cs_ok:
            print("\nOne equivalent serial order:")
            print(" -> ".join(f"T{t}" for t in serial_order))
        else:
            if cycle_path:
                print("\nCycle detected in precedence graph:")
                print(" -> ".join(f"T{t}" for t in cycle_path))

        print("\n============================================\n")


if __name__ == "__main__":
    main()