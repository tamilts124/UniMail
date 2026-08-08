#!/usr/bin/env python3
"""Fix non-UTF8 bytes in cli_tempmailo_com.py by replacing Windows-1252 chars."""
import sys

fname = r'D:\ClaudeDir\tempmail\cli_tempmailo_com.py'

with open(fname, 'rb') as f:
    data = f.read()

bad = [(i, data[i]) for i in range(len(data)) if data[i] > 127]
print(f"Found {len(bad)} non-ASCII bytes:")
for off, b in bad:
    line_num = data[:off].count(b'\n') + 1
    ctx = data[max(0,off-40):off+30]
    print(f"  offset={off}, line={line_num}, byte=0x{b:02x}")
    print(f"  context: {ctx!r}")
    print()

# Replace Windows-1252 chars with ASCII equivalents
# 0x97 = em-dash → " — "
# 0x92 = right single quote → '
# 0x96 = en-dash → "-"
replacements = {
    0x97: b' - ',   # em-dash
    0x96: b'-',     # en-dash
    0x92: b"'",     # right single quote
    0x91: b"'",     # left single quote
    0x93: b'"',     # left double quote
    0x94: b'"',     # right double quote
    0x85: b'...',   # ellipsis
}

result = bytearray()
i = 0
while i < len(data):
    b = data[i]
    if b > 127:
        repl = replacements.get(b)
        if repl:
            result.extend(repl)
            print(f"Replaced 0x{b:02x} at offset {i} with {repl!r}")
        else:
            result.extend(b'?')
            print(f"Unknown byte 0x{b:02x} at offset {i}, replaced with '?'")
    else:
        result.append(b)
    i += 1

with open(fname, 'wb') as f:
    f.write(bytes(result))
print(f"\nFixed {len(bad)} bytes. File saved.")
