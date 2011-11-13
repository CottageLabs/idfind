import urllib2
from datetime import datetime
from cStringIO import StringIO

import whatid.dao
import whatid.util as util

class Importer(object):
    def __init__(self, owner):
        self.owner = owner

    def submit(self, request):
        '''Import a regex or an identifer description into the database.'''
        pre = request.values.get("url",'')
        if not pre.endswith('/'):
            pre += '/'
        if not ( pre.startswith('http://') or pre.startswith('https://') ):
            pre = 'http://' + pre
        record = {
            "name": request.values["name"],
            "regex": request.values["regex"],
            "url_prefix": pre,
            "url_suffix": request.values["suffix"],
            "description": request.values["description"],
			# TODO: refactor useful links handling below (and perhaps submit.html template) to allow for multiple useful links
			"useful_links": request.values["useful_link1"],
            "tags": request.values["tags"].split(","),
            "timestamp": datetime.now().isoformat(),
            "owner": self.owner.id
        }
        if request.values["type"] == "regex":
            whatid.dao.Test.upsert(record)
        if request.values["type"] == "identifier":
            whatid.dao.Description.upsert(record)
        
