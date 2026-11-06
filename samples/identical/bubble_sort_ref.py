"""Tri à bulles — référence de base (Python)."""


def bubble_sort(arr):
    """Trie un tableau par le méthode des bulles."""
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


if __name__ == "__main__":
    data = [64, 34, 25, 12, 22, 11, 90]
    print("Tableau trié :", bubble_sort(data))
