"""Tri à bulles — version avec boucle for remplacée par while."""


def bubble_sort(arr):
    """Trie un tableau par la méthode des bulles (boucles while)."""
    n = len(arr)
    i = 0
    while i < n:
        j = 0
        while j < n - i - 1:
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
            j += 1
        i += 1
    return arr


if __name__ == "__main__":
    data = [64, 34, 25, 12, 22, 11, 90]
    print("Tableau trié :", bubble_sort(data))
