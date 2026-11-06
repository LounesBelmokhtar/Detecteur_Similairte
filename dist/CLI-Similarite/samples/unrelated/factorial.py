"""Factorielle récursive — algorithme sans rapport avec le tri à bulles."""


def factorial(n):
    """Calcule n! (factorielle) par récursion."""
    if n <= 1:
        return 1
    return n * factorial(n - 1)


def factorial_iterative(n):
    """Calcule n! de façon itérative."""
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


if __name__ == "__main__":
    print("5! =", factorial(5))
    print("7! =", factorial_iterative(7))
