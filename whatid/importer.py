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
            record = {}
        if request.values["type"] == "identifier":
            record = {}
        # here we should call dao.upsert to save our record
        pass



