import urllib2
from datetime import datetime
from cStringIO import StringIO

import whatid.dao
import whatid.util as util

class Importer(object):
    def __init__(self, owner):
        self.owner = owner

    def submit(self, request):
        '''Import an identifer test or description into the index.'''
        pre = request.values.get("url_suffix",'')
        useful_links = [request.values.get("useful_link1",'')]
        if not pre.endswith('/'):
            pre += '/'
        if not ( pre.startswith('http://') or pre.startswith('https://') ):
            pre = 'http://' + pre
        record = {
            "name": request.values.get("name",''),
            "regex": request.values.get("regex",''),
            "url_prefix": pre,
            "url_suffix": request.values.get("url_suffix",''),
            "description": request.values.get("description",''),
			# TODO: refactor useful links handling below (and perhaps submit.html template) to allow for multiple useful links
			"useful_links": useful_links,
            "tags": request.values.get("tags",'').split(","),
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "owner": self.owner.id
        }
        if request.values["type"] == "regex":
            whatid.dao.Test.upsert(record)
        if request.values["type"] == "description":
            whatid.dao.Description.upsert(record)
        
