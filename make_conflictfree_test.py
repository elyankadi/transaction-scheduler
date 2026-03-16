# generate_conflict_free_multiorder.py

n = 500

t1 = " ".join([f"w1[a{i}]" for i in range(1, n + 1)]) + " c1"
t2 = " ".join([f"w2[b{i}]" for i in range(1, n + 1)]) + " c2"
t3 = " ".join([f"w3[c{i}]" for i in range(1, n + 1)]) + " c3"

print("T1:")
print(t1)
print()
print("T2:")
print(t2)
print()
print("T3:")
print(t3)
