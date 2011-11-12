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
        if request.values["type"] == "regex":
            record = {
						"regex": request.values["regex"],
						"url_prefix": request.values["url"],
						"url_suffix": request.values["suffix"],
						"description": request.values["description"],
						"tags": request.values["tags"].split(","),
						"timestamp": datetime.now().isoformat()
					}
        if request.values["type"] == "identifier":
            record = {
						"url-service": request.values["url"],
						"url-service-suffix": request.values["suffix"],
						"description": request.values["description"],
						"tags": request.values["tags"].split(","),
						"timestamp": datetime.now().isoformat()
					}
        # here we should call dao.upsert to save our record
        whatid.dao.Test.upsert(record)