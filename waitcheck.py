import time, subprocess

for i in range(3):
    time.sleep(25)
    r = subprocess.run(
        ['python', 'unimail.py', '--list-message', 'testclaude@spymail.one'],
        capture_output=True, text=True, cwd=r'D:\ClaudeDir\tempmail'
    )
    out = r.stdout + r.stderr
    with open(r'D:\ClaudeDir\tempmail\mailcheck_result.txt', 'w') as f:
        f.write(f'Attempt {i+1}:\n{out}\n')
    if 'empty' not in out.lower():
        break
