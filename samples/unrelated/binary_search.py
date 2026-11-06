"""Recherche dichotomique — algorithme sans rapport avec le tri à bulles."""


def binary_search(arr, target):
    """Recherche dichotomique dans un tableau trié. Renvoie l'indice ou -1."""
    low = 0
    high = len(arr) - 1

    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1


if __name__ == "__main__":
    sorted_data = [2, 5, 8, 12, 16, 23, 38, 45, 67, 91]
    index = binary_search(sorted_data, 23)
    print("Indice trouvé :", index)
