#include <stdio.h>

int binary_search(int arr[], int size, int target) {
    int low = 0;
    int high = size - 1;
    while (low <= high) {
        int mid = (low + high) / 2;
        if (arr[mid] == target) {
            return mid;
        } else if (arr[mid] < target) {
            low = mid + 1;
        } else {
            high = mid - 1;
        }
    }
    return -1;
}

int main(void) {
    int sortedData[] = {2, 5, 8, 12, 16, 23, 38, 45, 67, 91};
    int n = sizeof(sortedData) / sizeof(sortedData[0]);
    printf("Indice : %d\n", binary_search(sortedData, n, 23));
    return 0;
}
