function gcd(a, b) {
    while (b !== 0) {
        const temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

function gcdRecursive(a, b) {
    if (b === 0) {
        return a;
    }
    return gcdRecursive(b, a % b);
}

console.log("PGCD(48, 18) = " + gcd(48, 18));
console.log("PGCD(100, 75) = " + gcdRecursive(100, 75));
