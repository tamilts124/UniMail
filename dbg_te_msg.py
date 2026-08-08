import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from cli_config import load_cache, set_debug
set_debug(True)
cache = load_cache()
from cli_tempemail import tempemail_get_message, tempemail_list_messages

msgs = tempemail_list_messages('naia2022@icmans.com', cache)
print(f"Messages: {len(msgs)}")
if msgs:
    msg_id = msgs[0].get('id')
    print(f"Getting message id={msg_id}")
    full = tempemail_get_message('naia2022@icmans.com', str(msg_id), cache)
    print("Full message keys:", list(full.keys()) if isinstance(full, dict) else type(full))
    print(json.dumps(full, indent=2, default=str)[:1000])
