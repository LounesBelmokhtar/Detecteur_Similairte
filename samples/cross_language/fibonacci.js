function fibRecursive(n) {
    if (n <= 1) {
        return n;
    }
    return fibRecursive(n - 1) + fibRecursive(n - 2);
}

function fibIterative(n) {
    let a = 0;
    let b = 1;
    for (let i = 0; i < n; i++) {
        let temp = a + b;
        a = b;
        b = temp;
    }
    return a;
}

console.log("Fib(10) = " + fibRecursive(10));
console.log("Fib(20) = " + fibIterative(20));
