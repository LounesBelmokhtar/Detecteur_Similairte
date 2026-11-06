"""Test de primalité — vérifie si un nombre est premier."""


def is_prime(n):
    """Retourne True si n est premier, False sinon."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


if __name__ == "__main__":
    for num in [2, 17, 20, 97, 100]:
        print(num, "→", "premier" if is_prime(num) else "composé")
