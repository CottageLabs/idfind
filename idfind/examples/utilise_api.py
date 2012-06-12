import requests # a slick HTTP request-making library
import json # IDFind can do JSON and HTML results, we want the JSON now

# your unknown string - e.g. could be retrieved from a PDF as part of text 
# mining from the "References" or "Bibliography" section
arbitrary_unknown = '10.1186/1758-2946-3-47'

# URL to IDFind query endpoint
idfind = 'http://localhost:5001/identify/'

# Need to tell IDFind we want a JSON result
# We're working on integrating the "Negotiatior" PyPi package, which reads the
# headers of a request to get the required content type, language and more.
req_suffix = '.json'

ans = requests.get(idfind + arbitrary_unknown + req_suffix)
ans = json.loads(ans.text)

# ans is now a Python construct (nested dicts and lists), we can (ab)use it!
# print json.dumps(ans, indent=4) # if you want to see the response's format

# Now, your unknown string could've been a part of multiple identifiers that
# we already know about - this will usually be a 1-item list, so you could do
# answer = ans['records']['hits']['hits'][0] below instead of the loop.
for answer in ans['records']['hits']['hits']:
    # Each record returned has information as to what that identifier could be
    for possible in answer['_source']['what']:
        # print json.dumps(possible, indent=4) # see all the available info
        print possible['name'] # just the name