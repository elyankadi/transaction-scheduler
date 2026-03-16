# Generate large conflict-free transactions

n = 1000

t1 = " ".join([f"w1[x{i}]" for i in range(1, n + 1)]) + " c1"
t2 = " ".join([f"r2[y{i}]" for i in range(1, n + 1)]) + " c2"

# Manual history with interleaving but still conflict-free
history_parts = ["s1", "s2"]

for i in range(1, n + 1):
    history_parts.append(f"w1[x{i}]")
    history_parts.append(f"r2[y{i}]")

history_parts.append("c1")
history_parts.append("c2")

history = " ".join(history_parts)

print("T1:")
print(t1)
print("\nT2:")
print(t2)
print("\nHISTORY:")
print(history)
