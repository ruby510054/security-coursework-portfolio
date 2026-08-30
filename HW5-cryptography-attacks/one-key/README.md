# One Key - RSA Onion With a Shared Private Exponent

**Category:** Cryptography (RSA)
**Techniques:** Common/shared private-exponent lattice attack, DFS search over lossy modular
**Difficulty (personal impression):** ★★★☆☆
truncation

## Objective
A flag is encrypted through 42 layers of RSA ("onion" encryption), each layer using a different
1024-bit modulus `n_i` but all 42 public exponents `e_i` derived from the **same** 481-bit private
key `d` (i.e. `e_i ≡ d^{-1} mod φ(n_i)`). Recover `d`, then peel all 42 layers to recover the flag.

## Approach
### Recovering the shared private key
Each key satisfies `e_i·d - k_i·φ(n_i) = 1` for some integer `k_i`, and since `φ(n_i) ≈ n_i`, this
is nearly `e_i·d - k_i·n_i ≈ 0` — a small-weight relation suited to lattice reduction. A basis
matrix with `e_i` in a weighted top row and `-n_i` on the diagonal is built for a subset of the
keys, and LLL finds a short vector encoding `d`. Using all 42 keys makes the lattice too large and
numerically unstable for LLL to finish in reasonable time; **20 keys** turned out to be the sweet
spot balancing a constraint strong enough to pin down `d` against a matrix small enough for LLL to
converge quickly. The recovered candidate `d` is verified by checking `(2^e mod n)^d ≡ 2 (mod n)`
against one of the public keys.

### Peeling the onion (handling lossy moduli)
Decrypting layer-by-layer with the recovered `d` initially produced garbage. The cause: since the
42 moduli `n_i` are **not** monotonically ordered by size, an inner ciphertext can be numerically
larger than the *next* layer's modulus, so encrypting it truncates information (`c mod n_i` loses
the `n_i`-multiple part). The fix is a depth-first search at each layer: after computing the base
decryption `m = c^d mod n_i`, try `m, m+n_i, m+2n_i, ...` as candidates (bounded by the *previous*
layer's modulus as an upper limit) and recurse into each, backtracking on candidates that don't
lead anywhere sensible. Reaching layer 0 successfully and finding printable flag-like bytes
confirms the correct path through the search tree.

## Key Takeaway
Two separate "gotchas" stacked in this challenge: a naive full-scale lattice attack needed to be
downsized to converge at all, and a textbook "just decrypt layer by layer" approach silently loses
data whenever an inner modulus happens to be smaller than an outer one — recognizing that as a
*lossy* transform (not just a decryption bug) is what motivated the DFS-based recovery.
