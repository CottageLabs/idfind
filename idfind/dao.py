import json
import uuid
import UserDict
import httplib
import logging
from datetime import datetime

import pyes
from werkzeug import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin

import idfind.identifier

requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

def init_db():
    conn, db = get_conn()
    try:
        conn.create_index(db)
    except pyes.exceptions.IndexAlreadyExistsException:
        pass

def get_conn():
    host = "127.0.0.1:9200"
    db_name = "idfind"
    conn = pyes.ES([host])
    return conn, db_name


class DomainObject(UserDict.IterableUserDict):
    # set __type__ on inheriting class to determine elasticsearch object
    __type__ = None

    def __init__(self, **kwargs):
        '''Initialize a domain object with key/value pairs of attributes.
        '''
        # IterableUserDict expects internal dictionary to be on data attribute
        self.data = dict(kwargs)

    @property
    def id(self):
        '''Get id of this object.'''
        return self.data.get('id', None)

    def save(self):
        '''Save to backend storage.'''
        # TODO: refresh object with result of save
        if 'modified' in self.data:
            self.data['modified'] = datetime.now().isoformat()
        return self.upsert(self.data)

    @classmethod
    def get(cls, id_):
        '''Retrieve object by id.'''
        conn, db = get_conn()
        try:
            out = conn.get(db, cls.__type__, id_)
            return cls(**out['_source'])
        except pyes.exceptions.ElasticSearchException, inst:
            if inst.status == 404:
                return None
            else:
                raise

    @classmethod
    def upsert(cls, data, state=None):
        '''Update backend object with a dictionary of data.
        If no id is supplied an uuid id will be created before saving.'''
        conn, db = get_conn()
        if 'id' in data:
            id_ = data['id']
        else:
            id_ = uuid.uuid4().hex
            data['id'] = id_
            
        if 'created' not in data and 'modified' not in data:
            data['created'] = datetime.now().isoformat()
            data['modified'] = datetime.now().isoformat()
            
        conn.index(data, db, cls.__type__, id_)
        return cls(**data)

    @classmethod
    def delete_by_query(cls, query):
        query = query.replace('/', '\/')

        url = "127.0.0.1:9200"
        loc = idfind + "/" + cls.__type__ + "/_query?q=" + query
        conn = httplib.HTTPConnection(url)
        conn.request('DELETE', loc)
        resp = conn.getresponse()
        return resp.read()
        
    @classmethod
    def query(cls, q='', terms=None, facet_fields=None, flt=False, **kwargs):
        '''Perform a query on backend.

        :param q: maps to query_string parameter.
        :param terms: dictionary of terms to filter on. values should be lists.
        :param facet_fields: we need a proper comment on this TODO
        :param kwargs: any keyword args as per
            http://www.elasticsearch.org/guide/reference/api/search/uri-request.html
        '''
        q = q.replace('/', '\/')

        conn, db = get_conn()
        if not q:
            ourq = pyes.query.MatchAllQuery()
        else:
            if flt:
                ourq = pyes.query.FuzzyLikeThisQuery(like_text=q,**kwargs)
            else:
                ourq = pyes.query.StringQuery(q, default_operator='AND')
        
        if terms:
            for term in terms:
                for val in terms[term]:
                    termq = pyes.query.TermQuery(term, val)
                    ourq = pyes.query.BoolQuery(must=[ourq,termq])
        
        ourq = ourq.search(**kwargs)
        if facet_fields:
            for item in facet_fields:
                ourq.facet.add_term_facet(item['key'], size=item.get('size',100), order=item.get('order',"count"))
        out = conn.search(ourq, db, cls.__type__)
        return out

    @classmethod
    def raw_query(self, query_string):
        query_string = query_string.replace('/', '\/')

        if not query_string:
            msg = json.dumps({
                'error': "Query endpoint. Please provide elastic search query parameters - see http://www.elasticsearch.org/guide/reference/api/search/uri-request.html"
                })
            return msg

        host = "127.0.0.1:9200"
        db_path = "idfind"
        fullpath = '/' + db_path + '/' + self.__type__ + '/_search' + '?' + query_string
        c =  httplib.HTTPConnection(host)
        c.request('GET', fullpath)
        result = c.getresponse()
        # pass through the result raw
        return result.read()

class Test(DomainObject):
    __type__ = 'test'
	
class Description(DomainObject):
    __type__ = 'description'
	
class Identifier(DomainObject):
    __type__ = 'identifier'
    
    @classmethod
    def identify(self, q):
        '''Tries to identify an identifier. Returns a list of dictionaries, each item in the list being an answer (a match for q). Returns None if there's no match.
        
        Works as follows: 1. try cache; 2. try tests in the index; 3. it's an unknown one.
        
        :param q: string to try to identify
        '''
        # try the cache first
        chits = self.query(q=q) # cache hits
        if chits['hits']['total'] != 0:
            return chits['hits']['hits'][0]['_source']['what']
            
        # try identification using the tests in the index
        engine = idfind.identifier.Identificator()
        answer = engine.identify(q)
        if answer:
            # save the identifier with its type
            result = {}
            result['what'] = answer
            result['identifier'] = q
            idfind.dao.Identifier.upsert(result)
            
        # neither cache search, nor regex identification succeeded
        else:
            # so now we'd like to record this identifier as "unknown"
            # but first, we'll check the list of unknown identifiers
            # so that we don't get duplicate records for the same id.
            unknowns = idfind.dao.UIdentifier.query(q=q)
            if unknowns['hits']['total'] == 0:
                # there are no such unknown identifiers, so put this one up
                idfind.dao.UIdentifier.upsert({'identifier':q})
        
        return answer
    
class UIdentifier(DomainObject):
    __type__ = 'uidentifier'

class Account(DomainObject, UserMixin):
    __type__ = 'account'

    def set_password(self, password):
        self.data['password'] = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.data['password'], password)

    @property
    def collections(self):
        colls = Collection.query(terms={
            'owner': [self.id]
            })
        colls = [ Collection(**item['_source']) for item in colls['hits']['hits'] ]
        return colls
        
class TwitterCreds(DomainObject):
    __type__ = 'twittercreds'

class TwitterLastID(DomainObject):
    __type__ = 'twitterlastid'
