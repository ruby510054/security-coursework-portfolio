# Security Coursework Portfolio

Write-ups and exploit scripts from my Software Security (Secure Programming) coursework, covering
binary exploitation, web security, reverse engineering, malware analysis, and applied cryptography.

Each folder contains only my own solving process and scripts — the original challenge
distributions (binaries, Dockerfiles, service source) are intentionally omitted. These challenges
are retired and no longer reused in the current offering of the course, so the full write-ups and
exploit code are shared here.

## Course Information

**Course:** Software Security (Secure Programming)
**Institution:** National Yang Ming Chiao Tung University (NYCU)
**Year:** 2025

## Contents

| Assignment | Category | Highlighted Techniques | Difficulty (personal impression) |
|---|---|---|---|
| [HW1](./HW1-mixed-ctf) | Mixed CTF | CBC padding oracle, LFSR + MT19937 state recovery, seccomp-sandboxed pwn, custom VM exploitation & reversing, blind NoSQL injection | ★★☆☆☆ |
| [HW2](./HW2-malware-analysis) | Malware Analysis | Ghidra static analysis, RC4 payload decryption, process-injection & C2 protocol reversing | ★★☆☆☆ |
| [HW3](./HW3-web-exploitation) | Web Exploitation | Format-string/CSP-bypass XSS with cross-session exfiltration, SSRF → cache poisoning → PHP deserialization chain | ★★★☆☆ |
| [HW4](./HW4-binary-exploitation) | Binary Exploitation | GOT-based arbitrary read/write, glibc 2.31/2.39 heap exploitation, File-Stream-Oriented Programming (House of Apple 2) | ★★★★★ |
| [HW5](./HW5-cryptography-attacks) | Cryptography | RSA related-message + O(1) factoring under a time limit, ECDSA biased-nonce lattice attack, RSA shared-exponent lattice attack | ★★★☆☆ |

## Tools

GDB / pwndbg, Ghidra, Wireshark, SageMath, z3 / gf2bv, `pwntools`, C, Python, Bash.

## A Note on Difficulty

The star ratings above (and in each individual challenge's README) are my own personal impression
of how demanding each assignment was, not a number pulled from class statistics. Ratings generally
track how much time each assignment actually took: HW4 (glibc heap exploitation) was the most
demanding of the set by a wide margin.

Treat this as a rough, subjective reference rather than a precise ranking — it reflects what I
personally found hard, which won't necessarily match how another student would rate the same
assignments.

## A Note on These Write-ups

These write-ups were reconstructed roughly a year after actually solving these challenges, based
on my own solving notes from the time and the reports I submitted for each assignment. I've tried
to keep every technical detail accurate against those original records, but some specifics may be
slightly off given the gap in time and memory.

## Note on Academic Integrity

These write-ups cover assignments from a course offering that no longer reuses these specific
challenges. If you're taking a similar course where these problems are still active, please solve
them yourself before reading further.
