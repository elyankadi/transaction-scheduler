n = 500

t1_ops = [f"w1[x{i}]" for i in range(1, n + 1)]
t2_ops = []
t3_ops = []

for i in range(1, n + 1):
    t2_ops.append(f"r2[x{i}]")
    t2_ops.append(f"w2[y{i}]")
    t3_ops.append(f"r3[y{i}]")

t1 = " ".join(t1_ops) + " c1"
t2 = " ".join(t2_ops) + " c2"
t3 = " ".join(t3_ops) + " c3"

history_parts = ["s1", "s2", "s3"]

for i in range(1, n + 1):
    history_parts.append(f"w1[x{i}]")
    history_parts.append(f"r2[x{i}]")
    history_parts.append(f"w2[y{i}]")
    history_parts.append(f"r3[y{i}]")

history_parts += ["c1", "c2", "c3"]
history = " ".join(history_parts)

print("T1:")
print(t1)
print("\nT2:")
print(t2)
print("\nT3:")
print(t3)
print("\nHISTORY:")
print(history)
