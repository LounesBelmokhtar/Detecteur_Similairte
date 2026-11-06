"""PGCD par la méthode d'Euclide — algorithme sans rapport avec le tri à bulles."""


def gcd(a, b):
    """Calcule le plus grand commun diviseur (Euclide itératif)."""
    while b != 0:
        a, b = b, a % b
    return a


def gcd_recursive(a, b):
    """Variante récursive du PGCD."""
    if b == 0:
        return a
    return gcd_recursive(b, a % b)


if __name__ == "__main__":
    print("PGCD(48, 18) =", gcd(48, 18))
    print("PGCD(100, 75) =", gcd_recursive(100, 75))
