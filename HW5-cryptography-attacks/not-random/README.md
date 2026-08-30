# Not Random - ECDSA Biased-Nonce Attack (Hidden Number Problem)

**Category:** Cryptography (ECDSA)
**Techniques:** Hidden Number Problem, lattice construction, LLL reduction
**Difficulty (personal impression):** ★★★☆☆

## Objective
Given four ECDSA (NIST P-384) signatures whose nonce `k` is biased (bounded by `B = 2^256`,
well below the curve's ~384-bit group order), recover the signing private key and use it (its low
128 bits, as an AES key) to decrypt the flag.

## Approach
Standard ECDSA algebra rearranges each signature into `k_i = t_i·d + u_i (mod q)` where
`t_i = s_i^{-1} r_i` and `u_i = s_i^{-1} z_i` are known and `|k_i| < B`. This is a textbook Hidden
Number Problem, solved by building a lattice whose short vector encodes the unknown nonces (and
implicitly the private key `d`), then finding that short vector with LLL.

The correct lattice basis (matching the Trail-of-Bits reference construction) is a `(d+2)x(d+2)`
matrix — the initial attempts used the wrong dimension and an unscaled `B/q` term, which is not
an integer and needs the whole matrix scaled (multiplying the diagonal blocks by `q`, and `t`/`u`
rows by `q`, turns `B/q` into a plain integer `B`). After correcting the construction, `fpylll`'s
`LLL.reduction` recovers a row containing the true nonces; from any one recovered `k_0`, the
private key follows directly as `d = r^{-1}(s·k_0 - z) mod q`. The low 128 bits of `d` are then
used as an AES-CTR key to decrypt the flag.

## Key Takeaway
The theoretical bound for this attack (`d >= n/l` signatures needed, where `l` is the number of
leaked/bounded bits) was satisfied from the start — the actual blocker was purely an
implementation detail (wrong lattice dimension and missing integer scaling), a good reminder to
verify a lattice construction against a known-correct reference before concluding an attack
"shouldn't" work.
