function binarySearch(arr, target) {
    let low = 0;
    let high = arr.length - 1;
    while (low <= high) {
        const mid = Math.floor((low + high) / 2);
        if (arr[mid] === target) {
            return mid;
        } else if (arr[mid] < target) {
            low = mid + 1;
        } else {
            high = mid - 1;
        }
    }
    return -1;
}

const sortedData = [2, 5, 8, 12, 16, 23, 38, 45, 67, 91];
console.log("Indice : " + binarySearch(sortedData, 23));
