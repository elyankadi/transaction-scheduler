n = 1000

# T1: writes x1..xn then commits
t1 = " ".join([f"w1[x{i}]" for i in range(1, n + 1)]) + " c1"

# T2: reads x1..xn then writes y1..yn then commits
t2 = " ".join(
    [f"r2[x{i}] w2[y{i}]" for i in range(1, n + 1)]
) + " c2"

# Valid serial history:
# T1 fully completes first, then T2 executes
history = "s1 " + " ".join([f"w1[x{i}]" for i in range(1, n + 1)]) + " c1 " \
        + "s2 " + " ".join([f"r2[x{i}] w2[y{i}]" for i in range(1, n + 1)]) + " c2"

print("T1:")
print(t1)
print("\nT2:")
print(t2)
print("\nHISTORY:")
print(history)
