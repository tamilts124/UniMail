import requests, json

# Check the session we sent email TO: bawypig1huzem4@mimimail.me
# That session's data from cache:
sid = "U2Vzc2lvbjp1GGAtfgNJzpjmp8-4O4kR"
token = "website_20260721We6cJPJUSV1vbg6m_ecde7176"

q = '{session(id:"%s"){addresses{address,mails{id,fromAddr,headerSubject,receivedAt,text}}}}' % sid
r = requests.post(f'https://dropmail.me/api/graphql/{token}', json={'query': q}, timeout=20)
print('HTTP', r.status_code)
d = r.json()
print(json.dumps(d, indent=2)[:1000])
