package com.example.urlshortener.util;

/**
 * Encodes non-negative long values into a compact Base62 string
 * ([0-9A-Za-z]) suitable for use as a URL-safe short code.
 */
public final class Base62Encoder {

    private static final String ALPHABET =
            "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    private static final int BASE = ALPHABET.length();

    private Base62Encoder() {
    }

    public static String encode(long value) {
        if (value == 0) {
            return String.valueOf(ALPHABET.charAt(0));
        }
        if (value < 0) {
            throw new IllegalArgumentException("Cannot Base62-encode a negative value: " + value);
        }

        StringBuilder sb = new StringBuilder();
        long remaining = value;
        while (remaining > 0) {
            int digit = (int) (remaining % BASE);
            sb.append(ALPHABET.charAt(digit));
            remaining /= BASE;
        }
        return sb.reverse().toString();
    }
}
