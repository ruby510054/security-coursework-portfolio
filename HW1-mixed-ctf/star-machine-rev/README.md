# STAR Machine (Reverse)

**Category:** Reverse Engineering
**Techniques:** Custom VM bytecode analysis, XOR-based serial verification
**Difficulty (personal impression):** ★★★★★

## Objective
Given a compiled StarVM bytecode program that verifies a 6-number serial, recover the input that
passes verification (the flag).

## Approach
Reused the StarVM instruction set knowledge from the companion pwn challenge to read the target
bytecode directly (rather than needing a disassembler): the program reads six numbers into its
context, then XORs each against a stored "expected" value and compares. Using GDB to dump the
context memory revealed the verification parameters, the expected values, and where user input
gets stored, all in one memory region. Since XOR is self-inverse, `xor.py` simply XORs the
recovered parameters against the expected values to compute the required input directly, then
formats the result as little-endian ASCII bytes to get the flag.

## Key Takeaway
Fully reverse-engineering a custom VM's ISA once (as in the pwn variant of this challenge) pays
off directly when a second challenge reuses the same VM — reading raw bytecode by hand becomes
tractable instead of needing to rebuild a disassembler from scratch.
