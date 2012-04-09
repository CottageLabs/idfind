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
        
        pre = request.values.get("url_prefix",'')
        if pre:
            if not pre.endswith('/'):
                pre += '/'
            if not ( pre.startswith('http://') or pre.startswith('https://') ):
                pre = 'http://' + pre
        
        resptest = request.values.get("resptest",'')
        if resptest:
            resptest_type = request.values.get("resptest_type",'')
            resptest_cond = request.values.get("resptest_cond",'')
        else:
            resptest_type = ''
            resptest_cond = ''
        
        useful_links = [request.values.get("useful_link1",'')]
            
        record = {
            "name": request.values['name'], # guaranteed to have 'name'
            "regex": request.values.get("regex",''),
            "url_prefix": pre,
            "url_suffix": request.values.get("url_suffix",''),
            "resptest": resptest,
            "resptest_type": resptest_type,
            "resptest_cond": resptest_cond,
            "description": request.values.get("description",''),
            # TODO: refactor useful links handling below (and perhaps submit.html template) to allow for multiple useful links
            "useful_links": useful_links,
            
            # for tags - return no empty strings as tags, trim whitespace on 
            # both ends of individual tags; but only check for empty strings
            # AFTER splitting and trimming the individual strings - prevents
            # things like "tag1, tag2, " from inserting an empty tag at the
            # end: e.g. don't want ["tag1", "tag2", ""]
            "tags": [final_tag for final_tag in [tag.strip() for tag in request.values.get("tags",'').split(",")] if final_tag], 
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "owner": self.owner.id,
            "ratings": [],
            "score_feedback": 0,
            "votes_feedback": 0
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
        
        # The below will crash and burn if there is test_id in the request we
        # got, and so it should - we can't know which test to rate without its
        # unique id in the index.
        test = idfind.dao.Test.get(request.values['test_id'])
        
        if 'ratings' not in test:
            test['ratings'] = []
        
        # append the rating dict to the other ratings received for this test
        test['ratings'].append(rating)
        # so you end up with a key "ratings" in the test's "_source" dictionary
        # and the value of that is a list of all received ratings, each of
        # which is in itself a dictionary
        
        # also modify the test's feedback-generated accuracy score and
        # increment total votes counter
        
        # preserve backwards compatibility so users don't have to delete their
        # ES indexes just because we've added an item to the "test" type
        if 'score_feedback' not in test:
            test['score_feedback'] = 0
        if 'votes_feedback' not in test:
            test['votes_feedback'] = 0
            
        if test_worked:
            test['score_feedback'] += 1
        else:
            test['score_feedback'] -= 1 # yes, it can go negative!
        
        test['votes_feedback'] += 1
        test.save()