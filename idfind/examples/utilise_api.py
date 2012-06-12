# Small example app which queries IDFind and uses prints info about the result
# Just run it from the command line with
# python utilise_api.py str1 "unknown string 2"
# and it will print results out (same order as the order of your parameters)
# It will take at least 1 (but also 2 or more) strings as arguments.

import argparse # for parsing command-line arguments in Python
import requests # a slick HTTP request-making library
import json # IDFind can do JSON and HTML results, we want the JSON now

parser = argparse.ArgumentParser(description='Query IDFind.')
parser.add_argument('query_strings', metavar='str', type=str, nargs='+',
                   help='query strings to throw at IDFind')

args = parser.parse_args()

# URL to IDFind query endpoint
idfind = 'http://idfind.cottagelabs.com/identify/'
# idfind = 'http://localhost:5001/identify/' # if you're coding on IDFind

# Need to tell IDFind we want a JSON result
# We're working on integrating the "Negotiatior" PyPi package, which reads the
# headers of a request to get the required content type, language and more.
req_suffix = '.json'

counter = 0
for unknown_str in args.query_strings:
    counter += 1

    ans = requests.get(idfind + unknown_str + req_suffix)
    ans = json.loads(ans.text)

    # ans is now a Python construct (nested dicts and lists), we can (ab)use it!
    # print json.dumps(ans, indent=4) # if you want to see the response's format

    # Now, your unknown string could've been a part of multiple identifiers.
    if ans['records']:
        for answer in ans['records']['hits']['hits']:
            # Each record returned has information as to what that identifier could be
            for possible in answer['_source']['what']:
                # print json.dumps(possible, indent=4) # see all the available info
                print str(counter) + '.', 'IDFind thinks', '"' + unknown_str + '"', 'is a', possible['name'] # just the name
    else:
        print str(counter) + '.', 'IDFind doesn\'t know what', '"' + unknown_str + '"', 'is. Sorry! Why don\'t you go to http://idfind.cottagelabs.com/submit and teach it?'