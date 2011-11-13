import httplib, json

f = open('data.json')
j = json.loads(f.read())

for r in j:
    print json.dumps(r)
    conn = httplib.HTTPConnection('localhost', '9200')
    fullpath = "/whatid/test"
    conn.request('POST', fullpath, json.dumps(r))
    print conn.getresponse().status