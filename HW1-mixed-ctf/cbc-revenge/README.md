# CBC Revenge

**Category:** Cryptography
**Techniques:** AES-CBC padding oracle, custom padding/checksum forgery
**Difficulty (personal impression):** ★★★☆☆

## Objective
Forge a ciphertext that the server accepts as valid to recover/produce the flag.

## Vulnerability
The service encrypts the flag with AES-128-CBC using a custom padding scheme
(`((rem - 1) << 4) | checksum` instead of standard PKCS#7) and exposes an oracle that decrypts a
supplied `IV || C1 || C2 || ...` and reports whether the padding and checksum are valid.

## Approach
Since CBC decryption is `P[i] = Intermediate[i] XOR C[i-1]`, modifying `C[i-1]` (or the IV) lets
an attacker control the decrypted plaintext byte-by-byte and probe the oracle for valid padding.
Because the checksum is unknown, `attack_server.py` (targeting one block at a time via
`BLOCK_TO_ATTACK`) enumerates all 16 possible single-byte-guess plaintexts consistent with a valid
padding response rather than a single unique answer, then a human picks the candidate that reads
as plausible flag text. Running the attack across both ciphertext blocks and concatenating the
recovered plaintext yields the full flag.

## Key Takeaway
A non-standard padding/checksum scheme doesn't defeat a padding oracle attack — it only changes
what "valid" looks like to the oracle, and enumerating candidates per block still works when the
oracle can't be made fully deterministic.
