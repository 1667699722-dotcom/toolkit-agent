import math

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(math.isqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

primes = [n for n in range(1, 101) if is_prime(n)]
prime_sum = sum(primes)
sqrt_sum = math.sqrt(prime_sum)

print(f"质数列表: {primes}")
print(f"质数个数: {len(primes)}")
print(f"质数之和: {prime_sum}")
print(f"和的平方根: {sqrt_sum:.3f}")
