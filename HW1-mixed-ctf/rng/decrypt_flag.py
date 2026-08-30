import sys
import pickle
import random
import struct


def load_rng1_state(filename):
    with open(filename, 'rb') as f:
        # Read format: obs_len (8) | L (8) | observed bits | C array
        obs_len = struct.unpack('Q', f.read(8))[0]
        L = struct.unpack('Q', f.read(8))[0]
        observed = [b for b in f.read(obs_len)]
        C = [b for b in f.read(L + 1)]

    return observed, L, C


def predict_rng1(observed, L, C, num_bits):
    if L == 0:
        return [0] * num_bits

    # State = last L observed bits
    state = list(observed[-L:])
    output = []

    for _ in range(num_bits):
        # Compute next bit
        nextb = 0
        for i in range(1, L + 1):
            if C[i]:
                nextb ^= state[L - i]

        output.append(nextb)

        # Shift state
        state = state[1:] + [nextb]

    return output


def load_rng2_state(filename):
    with open(filename, 'rb') as f:
        state = pickle.load(f)

    rng = random.Random()
    rng.setstate(state)
    return rng


def predict_rng2(rng, num_bits):
    return [rng.getrandbits(1) for _ in range(num_bits)]


def bits_to_bytes(bits):
    bytes_list = []
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits):
                byte = (byte << 1) | bits[i + j]
        bytes_list.append(byte)
    return bytes(bytes_list)


def bytes_to_bits(data):
    bits = []
    for byte in data:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits


def decrypt_flag(c_bytes, rng1_bits, rng2_bits):
    c_bits = bytes_to_bits(c_bytes)

    if len(rng1_bits) < len(c_bits) or len(rng2_bits) < len(c_bits):
        raise ValueError("Not enough predicted bits!")

    # XOR all three
    flag_bits = []
    for i in range(len(c_bits)):
        flag_bit = c_bits[i] ^ rng1_bits[i] ^ rng2_bits[i]
        flag_bits.append(flag_bit)

    return bits_to_bytes(flag_bits)


def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <c_hex.txt> <rng1_state.bin> <rng2_state.pkl>")
        print()
        print("Example:")
        print(f"  {sys.argv[0]} c_hex.txt rng1_state.bin rng2_state.pkl")
        return 1

    c_file = sys.argv[1]
    rng1_state_file = sys.argv[2]
    rng2_state_file = sys.argv[3]

    # Read encrypted flag
    with open(c_file, 'r') as f:
        c_hex = f.read().strip()

    c_bytes = bytes.fromhex(c_hex)
    print(f"  Encrypted flag: {len(c_bytes)} bytes")

    # Load RNG1 state
    observed, L, C = load_rng1_state(rng1_state_file)
    print(f"  Recovered LFSR degree: {L}")

    # Load RNG2 state
    rng2 = load_rng2_state(rng2_state_file)

    # Predict RNG outputs
    num_bits = len(c_bytes) * 8

    rng1_bits = predict_rng1(observed, L, C, num_bits)
    print(f"  Generated {len(rng1_bits)} bits from RNG1")

    rng2_bits = predict_rng2(rng2, num_bits)
    print(f"  Generated {len(rng2_bits)} bits from RNG2")

    # Decrypt flag
    flag = decrypt_flag(c_bytes, rng1_bits, rng2_bits)

    # Try to decode as UTF-8
    try:
        flag_str = flag.decode('utf-8', errors='ignore')
        print(flag_str)

        # Also show hex if it contains non-printable chars
        if any(b < 32 or b > 126 for b in flag):
            print("Flag (hex):")
            print(flag.hex())
    except:
        print("Flag (hex):")
        print(flag.hex())

    return 0


if __name__ == "__main__":
    sys.exit(main())
