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
            "name": request.values.get("name",''),
            "regex": request.values.get("regex",''),
            "url_prefix": pre,
            "url_suffix": request.values.get("url_suffix",''),
            "resptest": resptest,
            "resptest_type": resptest_type,
            "resptest_cond": resptest_cond,
            "description": request.values.get("description",''),
            # TODO: refactor useful links handling below (and perhaps submit.html template) to allow for multiple useful links
            "useful_links": useful_links,
            "tags": request.values.get("tags",'').split(","),
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "owner": self.owner.id
        }
        
        if request.values["test_or_desc"] == "test":
            idfind.dao.Test.upsert(record)
        if request.values["test_or_desc"] == "description":
            idfind.dao.Description.upsert(record)
        
    def rate(self, request):
        pass