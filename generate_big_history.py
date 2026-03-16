n = 1000

history = ["s1", "s2"]

for i in range(1, n + 1):
    history.append(f"w1[x{i}]")
    history.append(f"r1[y{i}]")
    history.append(f"r2[x{i}]")
    history.append(f"w2[z{i}]")

history.extend(["c1", "c2"])

print(" ".join(history))