# Cosmic Ray - RSA Related-Message Attack Under a Time Limit

**Category:** Cryptography (RSA)
**Techniques:** Franklin-Reiter related-message attack, resultant precomputation + Horner's
**Difficulty (personal impression):** ★★★☆☆
method, O(1)-per-guess factoring

## Objective
Given `n`, `e=17`, and `c1 = (d+δ1)^17 mod n`, `c2 = (d+δ2)^17 mod n` for a 2048-bit RSA key with
`δ1, δ2` unknown 20-bit "cosmic ray" noise values added to the private exponent `d`, forge a value
`x` with `x^0x1337 ≡ 42 (mod n)` — all within a **69-second** time budget.

## Approach
1. **Find `Δ = δ2 - δ1`** (one of ~2^21 candidates) via a Franklin-Reiter related-message attack:
   `x^e - c1` and `(x+Δ)^e - c2` share the root `m1 = d+δ1` exactly when `Δ` is correct, so their
   GCD becomes linear only at the right `Δ`. Computing a full polynomial GCD per candidate is far
   too slow for ~2 million candidates at 2048-bit modulus, so instead the **resultant**
   `h(y) = Res_x(x^e - c1, (x+y)^e - c2)` — a degree-289 polynomial in `y` alone — is precomputed
   *once*, and each candidate `Δ` is then just a single Horner's-method polynomial evaluation
   (no modular inverses needed per candidate), roughly a 2-3x speedup.
2. **Recover `m1`** from the correct `Δ` via one final polynomial GCD.
3. **Factor `n`** using `m1 ≈ d`: since `e·d ≡ 1 (mod λ(n))`, and `m1 = d + δ1` for unknown
   `δ1 < 2^20`, the candidate multiplier `k(noise) = e·(m1-noise) - 1` is checked with a
   Miller-Rabin-style test for a nontrivial square root of 1, giving `p, q`. The key optimization
   is computing `a^{k(noise)}` for each of the ~2^20 candidate `noise` values via a *single*
   modular multiplication per step (precomputing `a^(-e)` once) rather than a fresh modular
   exponentiation each time — turning an O(2^20 exponentiations) search into O(2^20
   multiplications).
4. **Compute the answer** as `42^(0x1337⁻¹ mod φ(n)) mod n` once `n` is factored.

Implemented with `gmpy2` for fast big-integer arithmetic and multiprocessing to parallelize the Δ
search across cores; the full attack completes in roughly 60 seconds.

## Key Takeaway
The generic version of an attack (recompute a full polynomial GCD, or a full modular
exponentiation, for every one of millions of candidates) is often asymptotically fine but
practically too slow — precomputing an equivalent single-variable polynomial (resultant) or an
incremental multiplicative step is what makes an otherwise-correct attack fit inside a hard wall
clock deadline.
