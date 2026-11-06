"""
Tri à bulles — copie reformatée avec commentaires ajoutés.
Le code est fonctionnellement identique mais visuellement différent.
"""

# Définition de la fonction de tri
def bubble_sort(arr):
    """
    Trie un tableau par la méthode des bulles.
    Complexité temporelle : O(n²).
    """
    # Récupération de la taille du tableau
    n = len(arr)
    # Boucle externe : nombre de passes
    for i in range(n):
        # Boucle interne : comparaisons adjacentes
        for j in range(0, n - i - 1):
            # Comparaison des éléments voisins
            if arr[j] > arr[j + 1]:
                # Échange (swap) en Python
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    # Retour du tableau trié (tri en place)
    return arr


# Point d'entrée du programme
if __name__ == "__main__":
    data = [64, 34, 25, 12, 22, 11, 90]
    print("Tableau trié :", bubble_sort(data))
