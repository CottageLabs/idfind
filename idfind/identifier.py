import re
import idfind.dao
import urllib2
from urllib2 import HTTPError, URLError
from datetime import datetime

class Identificator(object):
    def __init__(self): pass
    
    def identify(self, identifier):
        success = []
        # get all of the regular expressions
        d = {'start' : 0, 'size' : 100, 'sort':[{"score_feedback":"asc"}]};
        while True:
            regexes = idfind.dao.Test.query(**d)
            if len(regexes['hits']['hits']) == 0:
                break
            d = {'start' : d['start'] + d['size'], 'size' : 100}
            success += self._check_regexes(identifier, regexes['hits']['hits'])
        return success
        
    def _check_regexes(self, identifier, regexes):
        success = []
        for r in regexes:
            test_id = r['_id'] # needed to save auto-gen. stats to the ES index
            r = r['_source']
            i = {} # identifier object which will eventually go into the index
                   # if one of the identification attempts is successful

            match = self._check_expression(identifier, r)
            if match is None:
                continue
            
            # copy all relevant values from the test object
            # do not copy user-submitted feedback or automatic statistics
            dontcopy = ["ratings", "auto_succeeded", "score_feedback", "votes_feedback"]
            for key, value in r.items():
                if key not in dontcopy:
                    i[key] = value
            # set timestamps of identifier object (it's being created *now*)
            i['created'] = datetime.now().isoformat()
            i['modified'] = datetime.now().isoformat()
            
            if not r['url_prefix']:
                self._save_stats(test_id = test_id, test_success = True)
                success.append(i)
                continue
                
            id = self._extract_id(match)
            serviced = self._check_service(id, r)
            if serviced:
                self._save_stats(test_id = test_id, test_success = True)
                success.append(i)
                
        return success
    
    def _check_expression(self, identifier, regex):
        result = re.match(regex['regex'], identifier)
        return result
    
    def _extract_id(self, match):
        if match.groupdict().has_key("id"):
            return match.group("id")
        return match.group()
    
    def _check_service(self, identifier, r):
        url =  r['url_prefix'] + identifier + r['url_suffix']
        # print url
        try:
            urllib2.urlopen(url)
            return True
        except HTTPError as e:
            if (e.code == 401 or e.code == 403 or e.code == 402
                or e.code == 406 or e.code == 407):
                return True
            return False
        except URLError as e:
            # URL doesn't exist
            # (somebody has to check whether that particular code could mean other things like connection errors - I couldn't find a list of URLError code meanings... TODO
            if e.reason[0] == 11001:
                return False
    
    def _save_stats(self, test_id, test_success):
        '''Save automatically generated statistics to the Test document in the index.
        
        :param test_id: id of elasticsearch document to modify in the index
        :param test_success: did the regex match the user's string? True/False
        '''
        if test_success:
            test = idfind.dao.Test.get(test_id)
            test['auto_succeeded'] = test.data.get('auto_succeeded', 0) + 1
            test.save()
        # not doing anything if the test failed