import random


def generate_schedule(tx_ops, mode="random"):
    """
    Generate schedules using different strategies.

    Modes:
    - serial : execute transactions one after another
    - random : random interleaving (default)
    - interleave : force frequent switching between transactions
    """

    if mode == "serial":
        return generate_serial_schedule(tx_ops)

    if mode == "interleave":
        return generate_high_interleaving(tx_ops)

    return generate_random_schedule(tx_ops)


def generate_serial_schedule(tx_ops):
    """
    Serial schedule: T1 then T2 then ...
    """
    schedule = []

    for tid in sorted(tx_ops.keys()):
        for op in tx_ops[tid]:
            schedule.append(op.raw)

    return " ".join(schedule)


def generate_random_schedule(tx_ops):
    """
    Basic random interleaving preserving transaction order.
    """

    remaining = {tid: list(ops) for tid, ops in tx_ops.items()}
    schedule = []

    while any(remaining.values()):

        available = [tid for tid in remaining if remaining[tid]]
        tid = random.choice(available)

        op = remaining[tid].pop(0)
        schedule.append(op.raw)

    return " ".join(schedule)


def generate_high_interleaving(tx_ops):
    """
    Force strong interleaving between transactions
    to increase probability of conflicts.
    """

    remaining = {tid: list(ops) for tid, ops in tx_ops.items()}
    schedule = []

    tids = list(tx_ops.keys())
    random.shuffle(tids)

    while any(remaining.values()):

        for tid in tids:
            if remaining[tid]:
                op = remaining[tid].pop(0)
                schedule.append(op.raw)

        random.shuffle(tids)

    return " ".join(schedule)