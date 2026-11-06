"""Tri à bulles — version avec fonctions réordonnées et déclarations déplacées."""


def display_result(items):
    """Affiche le résultat du tri."""
    print("Tableau trié :", items)


def main():
    """Point d'entrée : orchestre l'exécution."""
    data = [64, 34, 25, 12, 22, 11, 90]
    bubble_sort(data)
    display_result(data)


# Fonction de tri déplacée à la fin du fichier
def bubble_sort(arr):
    """Trie un tableau par la méthode des bulles."""
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


if __name__ == "__main__":
    main()
