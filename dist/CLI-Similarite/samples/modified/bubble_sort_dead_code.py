"""Tri à bulles — version avec ajout de code mort et d'instructions inutiles."""

# Variables inutiles ajoutées
_UNUSED_FLAG = False
_TEMP_BUFFER = []
_DEBUG_COUNTER = 0

# Constante morte
LEGACY_THRESHOLD = 999999


def bubble_sort(arr):
    """Trie un tableau par la méthode des bulles (avec code mort)."""
    # Instruction morte : réassignation immédiate
    n = len(arr)
    n = n  # auto-affectation inutile
    _DEBUG_COUNTER = 0

    for i in range(n):
        # Bloc mort : jamais exécuté (condition toujours fausse)
        if _UNUSED_FLAG and LEGACY_THRESHOLD < 0:
            _TEMP_BUFFER.append(i)
            return None
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                _DEBUG_COUNTER += 1
    return arr


def dead_helper_function(x):
    """Fonction morte jamais appelée."""
    return x * 0 + LEGACY_THRESHOLD


if __name__ == "__main__":
    data = [64, 34, 25, 12, 22, 11, 90]
    print("Tableau trié :", bubble_sort(data))
    # dead_helper_function(42)  # jamais appelé
