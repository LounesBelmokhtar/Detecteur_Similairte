"""Tri à bulles — version avec renommage complet de toutes les variables et fonctions."""


def sorter_algorithm(sequence):
    """Trie une séquence par la méthode des bulles (renommage intégral)."""
    size = len(sequence)
    for pass_idx in range(size):
        for compare_idx in range(0, size - pass_idx - 1):
            if sequence[compare_idx] > sequence[compare_idx + 1]:
                sequence[compare_idx], sequence[compare_idx + 1] = sequence[compare_idx + 1], sequence[compare_idx]
    return sequence


if __name__ == "__main__":
    input_data = [64, 34, 25, 12, 22, 11, 90]
    print("Résultat :", sorter_algorithm(input_data))
