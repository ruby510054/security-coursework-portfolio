from pwn import *

server_process = None
original_iv = None
original_ct = None


def oracle(iv_block, ct_block, verbose=False):
    payload = (iv_block + ct_block).hex()

    if verbose:
        print(f"        Sending: IV={iv_block.hex()[:32]}...")
        print(f"                 CT={ct_block.hex()[:32]}...")

    server_process.sendline(payload.encode())
    response = server_process.recvline().decode().strip()

    if verbose:
        print(f"        Response: {response}")

    return "Well received" in response


def attack_byte_position_optimized(iv_original, ct_block, position, known_intermediates, verbose_level=0):
    """
    Returns:
        Single intermediate value (not a list of 16)
    """
    target_rem = 16 - position

    attempts = 0

    # Try all possible intermediate values
    for intermediate_guess in range(256):
        # Try all possible checksums
        for checksum in range(16):
            target_byte = ((target_rem - 1) << 4) | checksum

            # Build modified IV
            iv_modified = bytearray(iv_original)
            iv_modified[position] = intermediate_guess ^ target_byte

            # Set all bytes after this position to match target_byte
            for pos in range(position + 1, 16):
                if pos in known_intermediates:
                    iv_modified[pos] = known_intermediates[pos] ^ target_byte
                else:
                    if verbose_level >= 1:
                        print(f"ERROR: Missing intermediate for position {pos}")
                    return None

            attempts += 1

            # Show first few attempts in detail
            show_detail = (verbose_level >= 2 and attempts <= 3)

            if show_detail:
                print(f"\n  Attempt {attempts}:")
                print(f"    Intermediate guess: 0x{intermediate_guess:02x}")
                print(f"    Checksum: 0x{checksum:x}")
                print(f"    Target byte: 0x{target_byte:02x}")

            if oracle(bytes(iv_modified), ct_block, verbose=show_detail):
                # Found it! Return immediately
                if verbose_level >= 1:
                    print(f"  ✓ Found after {attempts} attempts!")
                    print(f"    Intermediate[{position}] = 0x{intermediate_guess:02x}")
                    print(f"    First valid checksum: 0x{checksum:x}")

                return {
                    'intermediate': intermediate_guess,
                    'first_checksum': checksum,
                    'attempts': attempts
                }

            # Progress indicator
            if verbose_level >= 1 and attempts % 1000 == 0:
                print(f"  [{attempts:5d}] Searching...")

    # Not found
    if verbose_level >= 1:
        print(f"  ✗ No valid intermediate found after {attempts} attempts")

    return None


def decrypt_n_bytes_optimized(iv_original, ct_block, num_bytes, verbose_level=1):
    print(f"IV: {iv_original.hex()}")
    print(f"CT: {ct_block.hex()}")

    if num_bytes < 1 or num_bytes > 16:
        print(f"ERROR: num_bytes must be between 1 and 16")
        return None

    start_position = 15
    end_position = 16 - num_bytes

    intermediates = {}
    first_checksums = {}
    total_attempts = 0

    # Attack from right to left
    for position in range(start_position, end_position - 1, -1):
        print(f"Position {position}/{start_position} (byte {start_position - position + 1}/{num_bytes})")

        result = attack_byte_position_optimized(
            iv_original,
            ct_block,
            position,
            intermediates,
            verbose_level=verbose_level
        )

        if result is None:
            print(f"✗ Failed at position {position}")
            return None

        intermediates[position] = result['intermediate']
        first_checksums[position] = result['first_checksum']
        total_attempts += result['attempts']

        # Show progress
        if verbose_level >= 1:
            progress_str = ""
            for pos in range(16):
                if pos in intermediates:
                    # Calculate plaintext with first checksum found
                    pt = intermediates[pos] ^ iv_original[pos]
                    if 32 <= pt < 127:
                        progress_str += chr(pt)
                    else:
                        progress_str += '?'
                else:
                    progress_str += '.'
            print(f"  Progress: '{progress_str}'")

    print(f"\nSUCCESS! Total attempts: {total_attempts}")

    return {
        'intermediates': intermediates,
        'first_checksums': first_checksums,
        'total_attempts': total_attempts
    }


def derive_all_candidates(result, iv_original):
    intermediates = result['intermediates']
    positions = sorted(intermediates.keys())

    candidates = []

    # For each possible checksum offset (0 to 15)
    for chk_offset in range(16):
        plaintext = {}

        for pos in positions:
            base_intermediate = intermediates[pos]

            adjusted_intermediate = base_intermediate ^ chk_offset
            plaintext[pos] = adjusted_intermediate ^ iv_original[pos]

        # Build plaintext bytes
        pt_bytes = [plaintext[pos] for pos in positions]
        pt_hex = ''.join(f'{b:02x}' for b in pt_bytes)
        pt_str = ''.join(chr(b) if 32 <= b < 127 else f'\\x{b:02x}' for b in pt_bytes)

        candidates.append({
            'chk_offset': chk_offset,
            'plaintext': plaintext,
            'hex': pt_hex,
            'string': pt_str
        })

    return candidates


def display_candidates(candidates):
    for idx, cand in enumerate(candidates):
        print(f"[{idx+1:2d}] '{cand['string']}'")
        print(f"     Hex: {cand['hex']}")
        print(f"     Checksum offset: 0x{cand['chk_offset']:x}")
        print()


def main():
    global server_process, original_iv, original_ct

    # ========== CONFIGURATION ==========
    # Connection settings
    USE_REMOTE = True        # True: connect to remote, False: use local server
    REMOTE_HOST = "10.113.0.1" # Remote server IP/hostname
    REMOTE_PORT = 35001       # Remote server port

    # Attack settings
    BLOCK_TO_ATTACK = 1       # Which block to attack (0, 1, 2, 3, ...)
    NUM_BYTES_TO_DECRYPT = 16  # How many bytes to decrypt (1-16)
    VERBOSE_LEVEL = 0         # 0=quiet, 1=normal, 2=detailed
    # ===================================

    print(f"Target: Block C[{BLOCK_TO_ATTACK}], Last {NUM_BYTES_TO_DECRYPT} byte(s)")

    # Connect to server
    if USE_REMOTE:
        print(f"Connecting to remote server: {REMOTE_HOST}:{REMOTE_PORT}")
        try:
            server_process = remote(REMOTE_HOST, REMOTE_PORT)
            print("✓ Connected!")
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return
    else:
        print("Starting local server...")
        server_process = process(['python3', 'server.py'])

    initial = server_process.recvline().decode().strip()
    print(f"Received: {initial[:64]}...")

    data = bytes.fromhex(initial)
    original_iv = data[:16]
    original_ct = data[16:]

    ct_blocks = [original_ct[i:i+16] for i in range(0, len(original_ct), 16)]

    print(f"Total blocks: {len(ct_blocks) + 1} (1 IV + {len(ct_blocks)} CT)")
    print(f"IV:  {original_iv.hex()}")
    for i, b in enumerate(ct_blocks):
        print(f"C[{i}]: {b.hex()}")

    # Validate block number
    if BLOCK_TO_ATTACK < 0 or BLOCK_TO_ATTACK >= len(ct_blocks):
        print(f"ERROR: Block {BLOCK_TO_ATTACK} doesn't exist!")
        print(f"Valid range: 0 to {len(ct_blocks) - 1}")
        server_process.close()
        return

    if BLOCK_TO_ATTACK == 0:
        iv_to_use = original_iv
        iv_name = "original IV"
    else:
        iv_to_use = ct_blocks[BLOCK_TO_ATTACK - 1]
        iv_name = f"C[{BLOCK_TO_ATTACK - 1}]"

    ct_to_attack = ct_blocks[BLOCK_TO_ATTACK]

    print(f"  Modifiable 'IV': {iv_name}")

    result = decrypt_n_bytes_optimized(iv_to_use, ct_to_attack, NUM_BYTES_TO_DECRYPT, VERBOSE_LEVEL)

    if result is None:
        print("\n✗ Attack failed!")
        server_process.close()
        return

    candidates = derive_all_candidates(result, iv_to_use)

    display_candidates(candidates)

    server_process.close()


if __name__ == "__main__":
    main()
