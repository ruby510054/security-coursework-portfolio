#!/usr/bin/env python3
from hashlib import sha256
from Crypto.Cipher import AES
from fpylll import IntegerMatrix, LLL, BKZ, GSO
from fpylll.algorithms.bkz2 import BKZReduction
import gmpy2
from gmpy2 import mpz

# P-384 curve order (NIST standard)
q = 39402006196394479212279040100143613805079739270465446667946905279627659399113263569398956308152294913554433653942643

# Signatures and messages
sigs = [
    (439466984244556297836955027962075494068111897267493274652013936909865855963925172887770398609453822698046470141968,
     12688214135249352463448347907973349419434869788829072791318493259402827088612671955967108221849081200403097252113952),
    (5213132559509325630360067691624138030043889782236709042506945661619145303705979952137555908359307570344902332623814,
     34913789473835125515865536615500951595689820825465574424919323137533074749513972075124212989224159874275538713053313),
    (16837774656865790250525711083651320547412706513406518515115905509572913267046579547895420452500864437009493477780094,
     20029939263395674736349579264090235514607748285299378154193414785894784684485857586294281789663330285135172860084016),
    (32949775214749405338348840756175978687084842150217194208919294140991271135711416322597818131090445944238069986255221,
     17941995812490591927576124175281036781859780405720340499139578554610923582590340653528314389779038549773488871739406)
]

msgs = [
    b"https://www.youtube.com/watch?v=3RuCaE5ciNU",
    b"https://www.youtube.com/watch?v=t0xj5ZxWU3c",
    b"https://www.youtube.com/watch?v=lpPih3tTuM0",
    b"https://www.youtube.com/watch?v=RR0gRA0vhrI",
]

ct = b'\xb4\x1ej\xf7\xfd\x92.\xc2\xa6\xb4\xce\xac6\x00p\t\xe5[\xf1\x81\xd8gK\x01\x83\x9cl\x12\xa7G\x1a\x8c\x1d\x05\xb8\xb7b\xfd\x04\xcb\x01\xc3\xe0ze\xe0\x1d\x17\xd4\x00B\x83\xbe\xb5r\x1a#\xf5T\x93\xa5'

B = 2**256  # Bound on nonces

def modinv(a, m):
    return int(gmpy2.invert(mpz(a), mpz(m)))

# Compute message hashes
zs = [int.from_bytes(sha256(msg).digest(), 'big') % q for msg in msgs]
rs = [sig[0] for sig in sigs]
ss = [sig[1] for sig in sigs]

# Compute t and u values: k = t*sk + u mod q
t_list = [(rs[i] * modinv(ss[i], q)) % q for i in range(4)]
u_list = [(zs[i] * modinv(ss[i], q)) % q for i in range(4)]


def check_solution(k0):
    """Check if k0 is valid and try to recover sk and flag"""
    if k0 <= 0 or k0 >= B:
        return None
    
    # sk = r^{-1} * (k*s - z) mod q
    sk = (modinv(rs[0], q) * (k0 * ss[0] - zs[0])) % q
    
    # Check all signatures
    for i in range(4):
        ki = (modinv(ss[i], q) * (zs[i] + rs[i] * sk)) % q
        if ki >= B:
            return None
    
    # Try decryption
    sk_lo = sk & ((1 << 128) - 1)
    key = sk_lo.to_bytes(16, 'big')
    try:
        cipher = AES.new(key, AES.MODE_CTR, nonce=ct[:8])
        pt = cipher.decrypt(ct[8:])
        if all(32 <= b < 127 or b in [0, 10, 13] for b in pt):
            return pt, sk
    except:
        pass
    return None

print("""
Trail of Bits matrix format:
| N   0   0   0   0     0 |
| 0   N   0   0   0     0 |
| 0   0   N   0   0     0 |
| 0   0   0   N   0     0 |
| t0  t1  t2  t3  B/N   0 |
| u0  u1  u2  u3  0     B |

Since we can't have B/N as integer, we multiply everything by N.
""")

# Create matrix with integer entries by scaling
d = 4
dim = d + 2

# Scale everything so B/q becomes B and B becomes B*q
M = IntegerMatrix(dim, dim)

for i in range(d):
    M[i, i] = q * q  # q becomes q^2 after scaling

for i in range(d):
    M[d, i] = t_list[i] * q  # t becomes t*q
M[d, d] = B  # B/q * q = B
M[d, d+1] = 0

for i in range(d):
    M[d+1, i] = u_list[i] * q  # u becomes u*q  
M[d+1, d] = 0
M[d+1, d+1] = B * q  # B becomes B*q

print("Running LLL on scaled matrix...")
LLL.reduction(M)

print("Checking for solutions...")
for i in range(dim):
    # The first component should be k*q (after scaling)
    k0_scaled = abs(M[i, 0])
    if k0_scaled % q == 0:
        k0 = k0_scaled // q
        if 0 < k0 < B:
            result = check_solution(k0)
            if result:
                pt, sk = result
                print(f"FOUND!")
                print(f"k0: {k0}")
                print(f"Flag: {pt}")
                exit(0)
    
    # Also check if it's directly k0 (without the q factor)
    k0 = k0_scaled
    if 0 < k0 < B:
        result = check_solution(k0)
        if result:
            pt, sk = result
            print(f"FOUND (direct)!")
            print(f"k0: {k0}")
            print(f"Flag: {pt}")
            exit(0)