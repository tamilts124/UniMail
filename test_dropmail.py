import requests, json, sys
token = 'website_20260721cXYcPvzZq8BpSb6U_3996acc8'
sid   = 'U2Vzc2lvbjp5BD1mfUdNZK4FC5OG_KuB'
q     = '{session(id:"%s"){addresses{address,mails{id,fromAddr,headerSubject,receivedAt}}}}' % sid
try:
    r = requests.post('https://dropmail.me/api/graphql/' + token, json={'query': q}, timeout=20)
    print('HTTP', r.status_code)
    print(json.dumps(r.json(), indent=2)[:800])
except Exception as e:
    print('ERROR:', e)
    sys.exit(1)
