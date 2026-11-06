function isPrime(n) {
    if (n < 2) {
        return false;
    }
    if (n < 4) {
        return true;
    }
    if (n % 2 === 0 || n % 3 === 0) {
        return false;
    }
    let i = 5;
    while (i * i <= n) {
        if (n % i === 0 || n % (i + 2) === 0) {
            return false;
        }
        i += 6;
    }
    return true;
}

const tests = [2, 17, 20, 97, 100];
for (const num of tests) {
    console.log(num + " → " + (isPrime(num) ? "premier" : "composé"));
}
