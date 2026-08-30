def xor_and_display(param, expected, position):
    """
    Args:
        param: The parameter value from context[0-5]
        expected: The expected value from context[6-11]
        position: Which number in the serial (1-6)
    """
    # Calculate the XOR result
    result = param ^ expected

    print(f"\nPosition {position}:")
    print(f"Parameter:  0x{param:016x}")
    print(f"Expected:   0x{expected:016x}")
    print(f"XOR Result: 0x{result:016x}")

    # Convert to bytes and try to interpret as ASCII (little-endian)
    result_bytes = result.to_bytes(8, byteorder='little')
    print(f"Bytes (LE): {' '.join(f'{b:02x}' for b in result_bytes)}")

    # Try to decode as ASCII, replacing non-printable characters
    ascii_le = ''.join(chr(b) if 32 <= b < 127 else f'\\x{b:02x}' for b in result_bytes)
    print(f"ASCII (LE): {ascii_le}")

    return result

# context[0-5] are the storage parameters
# context[6-11] are the expected verification values
context_params = [
    0x69be36747f876bae,  # context[0]
    0xb1f06aef794d1762,  # context[1]
    0x9d027f819959d8d5,  # context[2]
    0xc1c02a70aaf082a6,  # context[3]
    0x09d2ad94a3823f6d,  # context[4]
    0x4debb7d2337a4aca,  # context[5]
]

context_expected = [
    0x028a5b0f38c627e8,  # context[6]
    0xdcc3199c48294807,  # context[7]
    0xce5d4bdecb6a94b7,  # context[8]
    0xf0a7753dfca2c3f2,  # context[9]
    0x56a79dedfcf10c1b,  # context[10]
    0x4debb7af544e26ac,  # context[11]
]

# Calculate all six serial numbers
results = []
for i in range(6):
    result = xor_and_display(context_params[i], context_expected[i], i + 1)
    results.append(result)

# Try to concatenate all results as ASCII to see if it forms a flag
full_message_le = ""
for result in results:
    bytes_le = result.to_bytes(8, byteorder='little')
    chunk = ''.join(chr(b) if 32 <= b < 127 else '?' for b in bytes_le)
    full_message_le += chunk
print(f"\nReconstructed message: {full_message_le}")
