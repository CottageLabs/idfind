import urllib2
from datetime import datetime
from cStringIO import StringIO

import idfind.dao
import idfind.util as util

class Importer(object):
    def __init__(self, owner):
        self.owner = owner

    def submit(self, request):
        '''Import an identifer test or description into the index.'''
        
        
        # process multiple success response tests - up to 100
        # python, why you no have a better getlist() CGI iface function?!
        resptests = []
        resptest = {}
        for test_seq in range(0,100):
        
            next_resptest = 'resptests[' + str(test_seq) + ']'
            next_resptest_content = next_resptest + '[str]'

            if next_resptest_content in request.values:
                if request.values[next_resptest_content].strip():
                # is the content field filled for this line?
                    resptest['type'] = request.values[next_resptest + '[type]'].strip()
                    resptest['cond'] = request.values[next_resptest + '[cond]'].strip()
                    resptest['str'] = request.values[next_resptest_content].strip()
                    resptests.append(resptest.copy())
            else:
            # no more tests submitted
                break
                
        tmpl = self._clean_list(request.values.getlist('useful_links[]'))
        useful_links = []
        for link in tmpl:
            useful_links.append(self._prep_link(link))
            
        record = {
            "name": request.values['name'], # guaranteed to have 'name'
            "regex": request.values.get("regex",''),
            "url_prefix": self._prep_link(request.values.get("url_prefix",''), True),
            "url_suffix": request.values.get("url_suffix",''),
            "resptests": resptests,
            "description": request.values.get("description",''),
            "useful_links": useful_links,
            "tags": self._clean_list(request.values.get("tags",'').split(",")), 
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "owner": self.owner.id,
            "ratings": [],
            "score_feedback": 0,
            "votes_feedback": 0,
            "auto_succeeded": 0
        }
        
        # guaranteed to have 'test_or_desc'
        if request.values["test_or_desc"] == "test":
            idfind.dao.Test.upsert(record)
        if request.values["test_or_desc"] == "description":
            idfind.dao.Description.upsert(record)
	
    def rate(self, request):
        # construct a dictionary containing all the feedback information the
        # user gave us and some additional bits
        rating = {}
        rating['owner'] = self.owner.id
        rating['comment'] = request.values.get("comment", '')
        if request.values['test_worked'] == 'Yes':
            test_worked = True
        elif request.values['test_worked'] == 'No':
            test_worked = False
        rating['test_worked'] = test_worked
        rating['identifier'] = request.values.get("identifier_string", '')
        rating['created'] = datetime.now().isoformat()
        rating['modified'] = datetime.now().isoformat()
        
        # The below will crash and burn if there is no test_id in the request
        # we got, and so it should - we can't know which test to rate without
        # its unique id in the index.
        test = idfind.dao.Test.get(request.values['test_id'])
        
        # add the rating for this test
        test.data.setdefault('ratings',[]) # if there's no 'ratings' key, add it as an empty list
        test.data['ratings'].append(rating) # add the rating dict to the list of ratings
        
        # So, we end up with a key "ratings" in the test's "_source" dictionary
        # and the value of that is a list of all received ratings, each of
        # which is in itself a dictionary
        
        # also modify the test's feedback-generated accuracy score and
        # increment total votes counter
        if test_worked:
            test['score_feedback'] = test.data.get('score_feedback', 0) + 1
        else:
            test['score_feedback'] = test.data.get('score_feedback', 0) - 1 # yes, it can go negative!
        test['votes_feedback'] = test.data.get('votes_feedback', 0) + 1
        
        test.save()
        
    def _clean_list(self, list):
        '''Clean up a list coming from an HTML form. Returns a list.
        Returns an empty list if given an empty list.
        
        How to use: clean_list = self._clean_list(your_list), can use anywhere
        in this class where you've got a list.

        Example: you have a list of tags. This is coming in from the form
        as a single string: e.g. "tag1, tag2, ".
        You do tag_list = request.values.get("tags",'').split(",")
        Now you have the following list: ["tag1"," tag2", ""]
        You want to both trim the whitespace from list[1] and remove the empty
        element - list[2]. self._clean_list(tag_list) will do it.
        
        What it does (a.k.a. algorithm):
        1. Trim whitespace on both ends of individual strings
        2. Remove empty strings
        3. Only check for empty strings AFTER splitting and trimming the 
        individual strings (in order to remove empty list elements).
        '''
        # consider moving this method out to dao.py or somewhere where it can
        # be reused more easily - it is really generic
        return [clean_item for clean_item in [item.strip() for item in list] if clean_item]
        
    def _prep_link(self, link, endslash=False):
        '''Prepare a string which is meant to be a link (HTTP URL) for
        indexing. Puts http:// at the front if the string it's passed does not
        already start with http:// or https://.
        
        The endslash parameter is a Boolean which controls whether a forward
        slash '/' will be added to the string if the string doesn't already
        end with a '/'.
        
        Returns an empty string if passed an empty string (so you will never
        end up with 'http:///' or something of the sort).
        '''
        if link:
            if endslash and not link.endswith('/'):
                link += '/'
            if not ( link.startswith('http://') or link.startswith('https://') ):
                link = 'http://' + link
            
        return link