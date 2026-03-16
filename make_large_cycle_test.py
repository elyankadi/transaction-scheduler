n = 1000

# T1: w1[xi] r1[yi]
t1_ops = []
for i in range(1, n + 1):
    t1_ops.append(f"w1[x{i}]")
    t1_ops.append(f"r1[y{i}]")
t1_ops.append("c1")

# T2: r2[xi] w2[yi]
t2_ops = []
for i in range(1, n + 1):
    t2_ops.append(f"r2[x{i}]")
    t2_ops.append(f"w2[y{i}]")
t2_ops.append("c2")

# History: interleaving that creates cycle repeatedly
hist_ops = ["s1", "s2"]
for i in range(1, n + 1):
    hist_ops.append(f"w1[x{i}]")
    hist_ops.append(f"r2[x{i}]")
    hist_ops.append(f"w2[y{i}]")
    hist_ops.append(f"r1[y{i}]")
hist_ops.append("c1")
hist_ops.append("c2")

print("===== T1 =====")
print(" ".join(t1_ops))
print("\n===== T2 =====")
print(" ".join(t2_ops))
print("\n===== HISTORY =====")
print(" ".join(hist_ops))
