# RNG

**Category:** Cryptography
**Techniques:** LFSR state recovery (Berlekamp-Massey), MT19937 prediction
**Difficulty (personal impression):** ★★★☆☆

## Objective
The service outputs `RNG1(4096 bytes)`, `RNG2(4096 bytes)`, and `RNG1 xor RNG2 xor flag`. Recover
both generators' internal state well enough to reproduce their keystreams and extract the flag.

## Approach
`RNG1` is a combination of 21 XOR'd LFSRs; `RNG2` is Python's `random` module (MT19937), which
emits one bit at a time here. An initial attempt to model both generators as bit-vector
constraints and solve with `z3` was too slow in practice for the smallest (48-bit) LFSR alone.
Switching approach:
- **RNG1**: used the Berlekamp-Massey algorithm to recover the shortest LFSR (and thus its full
  internal state) directly from the observed output sequence, without needing to invert any
  cipher — implemented in `crack_a.c` for speed.
- **RNG2**: since the generator is a well-studied, widely reimplemented CSPRNG-adjacent PRNG,
  used a bit-vector (`gf2bv`) formulation of the MT19937 state-recovery problem (existing
  single-bit-output crackers like `randcrack` didn't support this one-bit-per-call output mode).
- With both internal states recovered, `crack_b.py` and `decrypt_flag.py` regenerate the
  keystreams and XOR them against the third output to recover the flag.

Pipeline: `split_output.py` → `crack_a` (LFSR state) → `crack_b.py` (MT19937 state) →
`decrypt_flag.py` (final XOR).

## Key Takeaway
Generic SAT/SMT solving doesn't scale to full internal-state recovery for these constructions —
picking the algorithm suited to each generator's structure (Berlekamp-Massey for LFSRs, a
dedicated bit-vector solver for MT19937) was necessary for it to finish in reasonable time.
