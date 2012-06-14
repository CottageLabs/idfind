import re
import idfind.dao
import requests
from requests import RequestException
from datetime import datetime

class Identificator(object):
    def __init__(self): pass
    
    def identify(self, identifier):
        success = []
        # get all of the regular expressions
        regexes = idfind.dao.Test.query()
        
        # Only proceed if there are actually any tests for us to run.
        # Need to do a separate query before the one below since the one below
        # will cause an elasticsearch exception if there are no tests in the
        # index, due to the 'sort' keyword argument.
        if regexes['hits']['total'] != 0:
            d = {'start' : 0, 'size' : 100, 'sort':[{"score_feedback":"asc"}]};
            while True:
                regexes = idfind.dao.Test.query(**d)
                if regexes['hits']['total'] == 0:
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
            i = r;
            # do not copy user-submitted feedback or automatic statistics + remove unique doc. id
            dontcopy = ["ratings", "auto_succeeded", "score_feedback", "votes_feedback", "id"]
            for del_key in dontcopy:
                if del_key in i:
                    del i[del_key]
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
        # TODO IMPORTANT: wrap this code in exception handling, if any user 
        # submits an invalid regex, NO identification can take place (since 
        # all tests are executed for every identifier, thus the invalid test 
        # is ALWAYS executed, causing IDFind to crash)
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
            req = requests.get(url)
            if r['resptests']:
                resptests_result = True
                for test in r['resptests']:
                    if test['type'] == 'header':
                        test_subject = req.headers.iteritems()
                    elif test['type'] == 'body':
                        # Convert the string to a list with 1 element,
                        # that element is a tuple with an empty 2nd value.
                        # This is the same format as the headers of a request.
                        # So now we can iterate over the content of a request
                        # using the same code for "header" and "body" type 
                        # tests - below.
                        test_subject = [(req.text,'')]
                        
                    for (k, v) in test_subject:
                        if test['cond'] == 'has':
                            if test['str'] in k or test['str'] in v:
                                resptests_result = resptests_result and True
                            else:
                                resptests_result = False
                                
                        if test['cond'] == 'has not':
                            if test['str'] not in k and test['str'] not in v:
                                resptests_result = resptests_result and True
                            else:
                                resptests_result = False
                return resptests_result
                        
            if req.status_code in [200, 401, 402, 403, 406, 407]:
                return True
            else:
                return False
        except RequestException as e:
            print e
            # something's wrong, e.g. nonexistent or malformed URL, timeout, etc.
            # TODO better handling of this - detect the different exceptions
            # Although what action would we take if we knew the exact error...?
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