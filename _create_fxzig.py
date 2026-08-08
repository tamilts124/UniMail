import sys,os; sys.path.insert(0,r'D:\ClaudeDir\tempmail'); os.chdir(r'D:\ClaudeDir\tempmail')
from cli_tempmailo_com import tempmailo_com_create_new
import random,string
# Force fxzig.com
from cli_tempmailo_com import TEMPMAILO_COM_DOMAINS
print("Available domains:", TEMPMAILO_COM_DOMAINS)
cache={"mailboxes":{}}
s,addr=tempmailo_com_create_new(cache)
print(f"ADDRESS:{addr}")
