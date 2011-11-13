import re
import whatid.dao
import urllib2
from urllib2 import HTTPError

class Identificator(object):
    def __init__(self): pass
    
    def identify(self, identifier):
        success = []
        # get all of the regular expressions
        d = {'start' : 0, 'size' : 100};
        while True:
            regexes = whatid.dao.Test.query(**d)
            if len(regexes['hits']['hits']) == 0:
                break
            d = {'start' : d['start'] + d['size'], 'size' : 100}
            success += self._check_regexes(identifier, regexes['hits']['hits'])
        return success
        
    def _check_regexes(self, identifier, regexes):
        success = []
        for r in regexes:
            r = r['_source']
            print r
            print identifier
            match = self._check_expression(identifier, r)
            if match is None:
                return success
            print match.group()
            if not r['url_prefix']:
                success.append(r)
                continue
            id = self._extract_id(match)
            serviced = self._check_service(id, r)
            if serviced:
                success.append(r)
        return success
    
    def _check_expression(self, identifier, regex):
        result = re.match(regex['regex'], identifier)
        return result
    
    def _extract_id(self, match):
        if match.groupdict().has_key("id"):
            return match.group("id")
        return match.group()
    
    def _check_service(self, identifier, r):
        url = r['url_prefix'] + identifier + r['url_suffix']
        try:
            urllib2.urlopen(url)
            return True
        except HTTPError as e:
            if (e.code == 401 or e.code == 403 or e.code == 402
                or e.code == 406 or e.code == 407):
                return True
            return False
