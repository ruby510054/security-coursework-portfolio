# Sc++

**Category:** Binary Exploitation
**Techniques:** Shellcode sandbox escape via seccomp-restricted return-to-win
**Difficulty (personal impression):** ★★★☆☆

## Objective
The binary runs a sandboxed shellcode runner that only allows the `exit`/`exit_group` syscalls.
Goal: get a shell and read the flag.

## Vulnerability
A `win()` function exists that spawns a shell, but its address is only known once the binary
(PIE) and stack canary are known at runtime, and the seccomp filter blocks any syscall a
shellcode payload could use directly.

## Approach
1. The sandboxed child process prints its exit code on termination, which leaks data: crafted
   shellcode that exits with the byte at a chosen stack offset lets the canary and a saved return
   address be leaked one byte at a time.
2. Used GDB to find that the canary lives at `rsp+0x70` and a known text address
   (`main+267`) lives at `rsp+0x30`; subtracting a fixed offset from that leaked address gives
   `win()`'s runtime address.
3. Built a payload: 24 bytes of padding, the leaked canary, 8 bytes of padding, then the computed
   address of `win()`, overwriting the saved return address to jump into `win()` once the current
   function returns.
4. `exploit_net.py` automates leaking the two values and sending the final payload, then reads
   `/flag.txt` from the resulting shell.

## Key Takeaway
A syscall allowlist (seccomp) only restricts what shellcode can *do* directly — it doesn't stop a
return-oriented jump into existing code the binary was already allowed to run, if the addresses
needed can be leaked another way (here, via the sandbox's own exit-code side channel).
