#include <stdio.h>

long factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

long factorial_iterative(int n) {
    long result = 1;
    for (int i = 2; i <= n; i++) {
        result *= i;
    }
    return result;
}

int main(void) {
    printf("5! = %ld\n", factorial(5));
    printf("7! = %ld\n", factorial_iterative(7));
    return 0;
}
