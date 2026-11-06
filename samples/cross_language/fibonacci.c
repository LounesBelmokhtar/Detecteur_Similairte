#include <stdio.h>

int fib_recursive(int n) {
    if (n <= 1) {
        return n;
    }
    return fib_recursive(n - 1) + fib_recursive(n - 2);
}

int fib_iterative(int n) {
    int a = 0;
    int b = 1;
    for (int i = 0; i < n; i++) {
        int temp = a + b;
        a = b;
        b = temp;
    }
    return a;
}

int main(void) {
    printf("Fib(10) = %d\n", fib_recursive(10));
    printf("Fib(20) = %d\n", fib_iterative(20));
    return 0;
}
