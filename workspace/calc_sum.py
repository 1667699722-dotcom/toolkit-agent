import math

k_values = list(range(1, 11))
result = 0
for k in k_values:
    term = math.sin(3) + math.cos(3 * k) * 2
    result += term
    print(f"k={k}: sin(3) + 2*cos({3*k}) = {math.sin(3):.6f} + 2*{math.cos(3*k):.6f} = {term:.6f}")

print(f"\n总和 = {result:.10f}")
