import sys,os; sys.path.insert(0,r'D:\ClaudeDir\tempmail'); os.chdir(r'D:\ClaudeDir\tempmail')
from cli_tempmailo_com import _tempmailo_com_new_session,_fetch_token,_tempmailo_com_pool,tempmailo_com_list_messages
a="znkghysyy@denipl.net"; cache={"mailboxes":{a:{}}}
s=_tempmailo_com_new_session(); tok=_fetch_token(s)
_tempmailo_com_pool[a]={"session":s,"token":tok}
cache["mailboxes"][a]={"tempmailo_com_token":tok,"tempmailo_com_address":a}
msgs=tempmailo_com_list_messages(a,cache)
print(f"COUNT:{len(msgs)}")
for m in msgs: print(f"MAIL:{m.get('from','?')}|{m.get('subject','?')}")
