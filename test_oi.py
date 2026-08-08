import json

f = open(r'D:\ClaudeDir\tempmail\har\openinbox.io.json', encoding='utf-8')
data = json.load(f)
f.close()
entries = data['log']['entries']
print(f'Total entries: {len(entries)}')
for e in entries:
    req = e['request']
    resp = e.get('response', {})
    url = req['url']
    status = resp.get('status', '?')
    # Show only non-static requests
    if any(x in url for x in ['api', 'inbox', 'email', 'message']):
        body = ''
        content = resp.get('content', {})
        if content.get('text'):
            body = content['text'][:100]
        print(f"{req['method']} {status} {url}")
        if body:
            print(f"   -> {body}")
