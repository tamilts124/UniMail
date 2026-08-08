#!/usr/bin/env python3
"""Poll tempmailo.com inbox for test email."""
import time, subprocess, sys

address = "iyjbggjntu@fxzig.com"
for attempt in range(1, 6):
    print(f"\n--- Attempt {attempt}/5 at {time.strftime('%H:%M:%S')} ---")
    result = subprocess.run(
        [sys.executable, "unimail.py", "--list-message", address],
        capture_output=True, text=True, cwd=r"D:\ClaudeDir\tempmail"
    )
    print(result.stdout)
    if "message(s) total" in result.stdout and "0 message" not in result.stdout:
        print("EMAIL RECEIVED!")
        break
    if attempt < 5:
        print(f"Empty, waiting 60s...")
        time.sleep(60)
else:
    print("No email received after 5 attempts.")
