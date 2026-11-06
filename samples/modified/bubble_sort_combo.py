"""Tri à bulles — combinaison de transformations : renommage + while + code mort + réordonnancement."""

# Variables mortes
_DIAG_MODE = False
_SCRATCH = []


def sort_in_place(sequence):
    """Trie la séquence par échange direct (renommage + while + code mort)."""
    size = len(sequence)
    idx = 0
    while idx < size:
        if _DIAG_MODE:
            _SCRATCH.append(idx)
        inner = 0
        while inner < size - idx - 1:
            if sequence[inner] > sequence[inner + 1]:
                tmp = sequence[inner]
                sequence[inner] = sequence[inner + 1]
                sequence[inner + 1] = tmp
            inner += 1
        idx += 1
    return sequence


def report(items):
    """Affiche le résultat (fonction déplacée vers le haut)."""
    print("Résultat :", items)


def driver():
    """Point d'entrée réordonné."""
    values = [64, 34, 25, 12, 22, 11, 90]
    sort_in_place(values)
    report(values)


if __name__ == "__main__":
    driver()
