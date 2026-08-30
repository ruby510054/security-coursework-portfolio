# Checker

**Category:** Reverse Engineering / Cryptography
**Techniques:** `rand()`-based cipher recovery via GDB
**Difficulty (personal impression):** ★★☆☆☆

## Objective
Find the input string that makes the checker binary print "yes" (the flag).

## Approach
The binary encrypts the user's input with a sequence of `rand()`-derived permutation and XOR
operations (no `srand()` call, so the sequence is fully deterministic) and compares the result
against a stored ciphertext. Since every step is invertible, the attack is a plain decryption:
1. Determined the expected plaintext length (34 bytes, including the null terminator) from the
   ciphertext length.
2. Used GDB to dump the actual permutation table and XOR table used at runtime.
3. Reimplemented the inverse of each step in `decrypt.py` using the recovered tables, applied to
   the ciphertext to recover the flag directly (no brute force needed).

## Key Takeaway
When a "custom encryption" is built purely from deterministic, invertible primitives with no
external randomness, the fastest path is usually to dump the exact runtime tables with a debugger
and write the inverse transform, rather than trying to brute-force or symbolically solve it.
