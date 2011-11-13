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
        record = {
            "name": request.value["name"],
            "regex": request.values["regex"],
            "url_prefix": request.values["url"],
            "url_suffix": request.values["suffix"],
            "description": request.values["description"],
            "tags": request.values["tags"].split(","),
            "timestamp": datetime.now().isoformat(),
            "owner": self.owner
        }
        if request.values["type"] == "regex":
            whatid.dao.Test.upsert(record)
        if request.values["type"] == "identifier":
            whatid.dao.Description.upsert(record)
        