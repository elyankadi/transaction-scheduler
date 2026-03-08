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
    explain_property
)

from analysis_serializability import (
    check_conflict_serializable,
    visualize_precedence_graph,
    explain_serializability
)

from schedule_generator import generate_schedule


def main():

    print("\n=================================================")
    print(" Transaction Scheduling & Correctness Analyzer")
    print("=================================================\n")

    while True:
        try:
            n = int(input("Enter number of transactions: ").strip())
            if n <= 0:
                print("Number of transactions must be positive.")
                continue
            break
        except ValueError:
            print("Please enter a valid integer.")

    tx_ops = {}

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
            print("\nTransaction definition invalid:")
            print(" -", e)
            return

        tx_ops[tid] = ops

    print("\nTransactions registered successfully.\n")

    # Display registered transactions
    print("--------------- Transactions ---------------")
    for tid in sorted(tx_ops.keys()):
        ops_str = " ".join(op.raw for op in tx_ops[tid])
        print(f"T{tid}: {ops_str}")
    print("--------------------------------------------\n")

    print("You may now test multiple schedules.")
    print("Type 'exit' to stop.\n")

    # ---------------- HISTORY LOOP ----------------
    while True:

        print("\nChoose schedule generation mode:")
        print("1 - Serial schedule (transactions executed one after another)")
        print("2 - Random interleaving")
        print("3 - Highly interleaved schedule (maximum concurrency)")
        print("4 - Manual schedule input")
        print("Type 'exit' to quit")

        mode = input("\nEnter option (1/2/3/4): ").strip().lower()

        if mode == "exit":
            print("\nExiting program.")
            break

        elif mode == "1":
            hist_str = generate_schedule(tx_ops, mode="serial")
            print("\nGenerated SERIAL schedule:")

        elif mode == "2":
            hist_str = generate_schedule(tx_ops, mode="random")
            print("\nGenerated RANDOM schedule:")

        elif mode == "3":
            hist_str = generate_schedule(tx_ops, mode="interleave")
            print("\nGenerated HIGHLY INTERLEAVED schedule:")

        elif mode == "4":
            hist_str = input("\nEnter HISTORY: ")

        else:
            print("\nInvalid option. Please choose 1, 2, 3, 4, or exit.\n")
            continue

        print("\n--------------- Schedule Under Analysis ---------------")
        print(hist_str)
        print("-------------------------------------------------------")

        try:
            history = parse_ops(hist_str)
            validate_history_against_transactions(history, tx_ops)

        except (ValidationError, ValueError) as e:
            print("\nInvalid history:")
            print(" -", e)
            print()
            continue

        print("\nHistory accepted. Running analysis...\n")

        # ---------- Correctness ----------
        reads_from, _ = compute_reads_from(history)

        rc_ok, rc_v = check_recoverable(history, reads_from)
        aca_ok, aca_v = check_aca(history, reads_from)
        strict_ok, strict_v = check_strict(history)
        rig_ok, rig_v = check_rigorous(history)

        print("--------------- Correctness Properties ---------------")

        explain_property("Recoverable (RC)", rc_ok, rc_v)
        explain_property("ACA", aca_ok, aca_v)
        explain_property("Strict", strict_ok, strict_v)
        explain_property("Rigorous", rig_ok, rig_v)

        print("------------------------------------------------------")

        # ---------- Conflict Serializability ----------
        cs_ok, graph, edge_reasons, topo_order, cycle_path = check_conflict_serializable(history)

        visualize_precedence_graph(graph)

        explain_serializability(cs_ok, graph, edge_reasons, topo_order, cycle_path)

        print("\n======================================================\n")


if __name__ == "__main__":
    main()