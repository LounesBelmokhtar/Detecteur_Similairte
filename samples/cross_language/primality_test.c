#include <stdio.h>
#include <stdbool.h>

bool is_prime(int n) {
    if (n < 2) {
        return false;
    }
    if (n < 4) {
        return true;
    }
    if (n % 2 == 0 || n % 3 == 0) {
        return false;
    }
    int i = 5;
    while (i * i <= n) {
        if (n % i == 0 || n % (i + 2) == 0) {
            return false;
        }
        i += 6;
    }
    return true;
}

int main(void) {
    int tests[] = {2, 17, 20, 97, 100};
    for (int k = 0; k < 5; k++) {
        printf("%d -> %s\n", tests[k], is_prime(tests[k]) ? "premier" : "compose");
    }
    return 0;
}
