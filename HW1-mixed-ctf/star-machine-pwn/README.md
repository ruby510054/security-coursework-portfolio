# STAR Machine (Pwn)

**Category:** Binary Exploitation
**Techniques:** Custom VM analysis, arbitrary read/write via VM opcodes
**Difficulty (personal impression):** ★★★★★

## Objective
`starvm` is a small stack-based bytecode VM. The goal is to get it to invoke a hidden
file-reading callback that prints the flag.

## Vulnerability
Two of the VM's opcodes (`READ_MEMORY` / `WRITE_MEMORY`, `0x14`/`0x13`) perform no bounds
checking: they let bytecode read or write any 8-byte slot of the VM's own context structure,
including its internal dispatch table.

## Approach
1. Used GDB to dump the VM's context memory (around `$rbp-0x29B0`) and map out its layout: the
   opcode dispatch table, the program counter, and a reserved-but-otherwise-unused function
   pointer slot at offset `0x10828` that a `SET_CALLBACK` opcode (`0x00`) populates with a
   function that decrypts and prints the contents of `/flag.txt` — but nothing in the VM's
   normal control flow ever calls it.
2. Computed the dispatch table's address relative to the context base, and used the unchecked
   `WRITE_MEMORY` opcode to overwrite one dispatch table entry (index `0x0D`) with the address of
   that flag-reading callback.
3. Built bytecode (`exploit.py` generates the payload, `send_payload.py` sends it) that pushes
   the callback address and target index onto the VM stack, writes it into the dispatch table,
   then executes opcode `0x0D` to trigger the newly-installed handler.

## Key Takeaway
A "safe" custom VM is only as safe as its weakest opcode — a single missing bounds check on a
memory-access instruction is enough to fully control the VM's own dispatch table and pivot into
otherwise-unreachable functionality.
