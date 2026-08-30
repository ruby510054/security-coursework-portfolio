import sys
import pickle
from time import perf_counter
import argparse
from gf2bv import LinearSystem
from gf2bv.crypto.mt import MT19937

def bytes_to_bits(data):
    bits = []
    for byte in data:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits

def bits_to_bytes(bits):
    bytes_list = []
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits):
                byte = (byte << 1) | bits[i + j]
        bytes_list.append(byte)
    return bytes(bytes_list)

def crack_rng2(observations, verbose=True):
    start = perf_counter()
    lin = LinearSystem([32] * 624)
    mt = lin.gens()
    rng = MT19937(mt)
    zeros = [rng.getrandbits(1) ^ obs for obs in observations]
    zeros.append(mt[0] ^ 0x80000000)  # Fix first bit
    if verbose:
        elapsed = perf_counter() - start
        print(f"  System created in {elapsed:.2f}s")
    start = perf_counter()
    solution = lin.solve_one(zeros)
    if verbose:
        elapsed = perf_counter() - start
        print(f"  Solved in {elapsed:.2f}s")
    if solution is None:
        raise RuntimeError("Failed to crack RNG2!")
    recovered_rng = MT19937(solution).to_python_random()
    for _ in range(len(observations)):
        recovered_rng.getrandbits(1)
    return recovered_rng

def predict_rng2(rng, num_bytes):
    bits = []
    for _ in range(num_bytes * 8):
        bits.append(rng.getrandbits(1))
    return bits_to_bytes(bits)

def read_hex_file_loose(path):
    with open(path, 'r') as f:
        text = f.read()
    hexdata = ''.join(text.split())
    if len(hexdata) % 2 != 0:
        raise ValueError("Hex data length is odd — invalid hex input.")
    return bytes.fromhex(hexdata)

def main():
    p = argparse.ArgumentParser(description="RNG2 Cracker - gf2bv MT19937 Attack")
    p.add_argument("input_file", help="hex file (e.g. b_hex.txt)")
    p.add_argument("state_file", help="output pickle file for RNG state")
    p.add_argument("--predict-bytes", "-p", type=int, default=0,
                   help="number of bytes to predict (default: 0 -> no prediction)")
    args = p.parse_args()

    input_file = args.input_file
    state_file = args.state_file
    predict_bytes = args.predict_bytes

    try:
        data = read_hex_file_loose(input_file)
    except Exception as e:
        print(f"Error reading hex file: {e}")
        return 2

    print(f"  Read {len(data)} bytes")

    bits = bytes_to_bits(data)
    print(f"  Converted to {len(bits)} bits")

    start = perf_counter()
    try:
        recovered_rng = crack_rng2(bits, verbose=True)
    except Exception as e:
        print(f"Crack failed: {e}")
        return 3
    total_time = perf_counter() - start
    print(f"  Total time: {total_time:.2f}s")

    with open(state_file, 'wb') as f:
        pickle.dump(recovered_rng.getstate(), f)
    print(f"Saved state to {state_file}")

    if predict_bytes > 0:
        predicted = predict_rng2(recovered_rng, predict_bytes)
        hex_str = predicted.hex()
        for i in range(0, len(hex_str), 64):
            print(hex_str[i:i+64])

    print("✓ RNG2 cracked successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
