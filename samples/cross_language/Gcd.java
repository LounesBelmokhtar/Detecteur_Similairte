public class Gcd {

    public static int gcd(int a, int b) {
        while (b != 0) {
            int temp = b;
            b = a % b;
            a = temp;
        }
        return a;
    }

    public static int gcdRecursive(int a, int b) {
        if (b == 0) {
            return a;
        }
        return gcdRecursive(b, a % b);
    }

    public static void main(String[] args) {
        System.out.println("PGCD(48, 18) = " + gcd(48, 18));
        System.out.println("PGCD(100, 75) = " + gcdRecursive(100, 75));
    }
}
