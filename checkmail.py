import time, subprocess, sys

for i in range(4):
    time.sleep(20)
    r = subprocess.run(
        ['python', 'unimail.py', '--list-message', 'bawypig1huzem4@mimimail.me'],
        capture_output=True, text=True, cwd=r'D:\ClaudeDir\tempmail'
    )
    out = r.stdout.strip()
    print(f'Attempt {i+1}: {out[:300]}', flush=True)
    sys.stdout.flush()
    if 'empty' not in out.lower() and 'message' in out.lower():
        print('GOT MAIL!', flush=True)
        break
print('CHECK DONE', flush=True)
