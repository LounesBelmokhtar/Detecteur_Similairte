"""Fibonacci récursif et itératif (Python)."""


def fib_recursive(n):
    """Calcule le n-ième nombre de Fibonacci par récursion."""
    if n <= 1:
        return n
    return fib_recursive(n - 1) + fib_recursive(n - 2)


def fib_iterative(n):
    """Calcule le n-ième nombre de Fibonacci de façon itérative."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


if __name__ == "__main__":
    print("Fib(10) =", fib_recursive(10))
    print("Fib(20) =", fib_iterative(20))
