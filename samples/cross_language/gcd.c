#include <stdio.h>

int gcd(int a, int b) {
    while (b != 0) {
        int temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

int gcd_recursive(int a, int b) {
    if (b == 0) {
        return a;
    }
    return gcd_recursive(b, a % b);
}

int main(void) {
    printf("PGCD(48, 18) = %d\n", gcd(48, 18));
    printf("PGCD(100, 75) = %d\n", gcd_recursive(100, 75));
    return 0;
}
