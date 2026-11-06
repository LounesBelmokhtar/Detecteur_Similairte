"""Témoins négatifs : algorithmes différents entre langages différents.

Ces fichiers servent de contrôles négatifs pour l'évaluation inter-langages :
un tri à bulles en Python comparé à une recherche dichotomique en Java
doit obtenir un score faible même au niveau 3.
"""

# Référence : tri à bulles (Python)
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
