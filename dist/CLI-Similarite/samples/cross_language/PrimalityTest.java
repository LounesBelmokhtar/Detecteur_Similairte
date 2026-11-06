public class PrimalityTest {

    public static boolean isPrime(int n) {
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

    public static void main(String[] args) {
        int[] tests = {2, 17, 20, 97, 100};
        for (int num : tests) {
            System.out.println(num + " → " + (isPrime(num) ? "premier" : "composé"));
        }
    }
}
