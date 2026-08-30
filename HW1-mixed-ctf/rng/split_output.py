import sys


def split_output(hex_data):
    data = bytes.fromhex(hex_data)
    total_len = len(data)

    print(f"Total data: {total_len} bytes")

    a_bytes = data[:4096]
    b_bytes = data[4096:8192]
    c_bytes = data[8192:]

    print(f"  a (RNG1):  {len(a_bytes)} bytes")
    print(f"  b (RNG2):  {len(b_bytes)} bytes")
    print(f"  c (flag):  {len(c_bytes)} bytes")

    a_hex = a_bytes.hex()
    b_hex = b_bytes.hex()
    c_hex = c_bytes.hex()

    return a_hex, b_hex, c_hex


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <output.hex>")
        print()
        print("Reads challenge output and splits into:")
        print("  - a_hex.txt (4096 bytes, RNG1)")
        print("  - b_hex.txt (4096 bytes, RNG2)")
        print("  - c_hex.txt (remaining, encrypted flag)")
        return 1

    input_file = sys.argv[1]

    with open(input_file, 'r') as f:
        hex_data = f.read().strip()

    hex_data = ''.join(hex_data.split())

    print(f"  Read {len(hex_data)} hex characters ({len(hex_data)//2} bytes)")

    a_hex, b_hex, c_hex = split_output(hex_data)

    with open('a_hex.txt', 'w') as f:
        f.write(a_hex)
    print("  ✓ Wrote a_hex.txt")

    with open('b_hex.txt', 'w') as f:
        f.write(b_hex)
    print("  ✓ Wrote b_hex.txt")

    with open('c_hex.txt', 'w') as f:
        f.write(c_hex)
    print("  ✓ Wrote c_hex.txt")

    print("✓ Output split successfully!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
