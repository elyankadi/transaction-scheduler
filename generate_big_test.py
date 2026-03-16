n = 1000

# Transaction 1
t1_ops = []
for i in range(1, n + 1):
    t1_ops.append(f"w1[x{i}]")
    t1_ops.append(f"r1[y{i}]")
t1_ops.append("c1")

# Transaction2
t2_ops = []
for i in range(1, n + 1):
    t2_ops.append(f"r2[x{i}]")
    t2_ops.append(f"w2[z{i}]")
t2_ops.append("c2")

print("T1:")
print(" ".join(t1_ops))
print()
print("T2:")
print(" ".join(t2_ops))
