import json
import uuid
import UserDict
import httplib

import pyes
from werkzeug import generate_password_hash, check_password_hash
from flaskext.login import UserMixin


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
        return self.upsert(self.data)

    @classmethod
    def get(cls, id_):
        '''Retrieve object by id.'''
        conn, db = get_conn()
        try:
            out = conn.get(db, cls.__type__, id_)
            print out['_source']
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
        conn.index(data, db, cls.__type__, id_)
        return cls(**data)

    @classmethod
    def delete_by_query(cls, query):
        url = "127.0.0.1:9200"
        loc = idfind + "/" + cls.__type__ + "/_query?q=" + query
        conn = httplib.HTTPConnection(url)
        conn.request('DELETE', loc)
        resp = conn.getresponse()
        return resp.read()
        
    @classmethod
    def query(cls, q='', terms=None, facet_fields=None, flt=False, notq=False, **kwargs):
        '''Perform a query on backend.

        :param q: maps to query_string parameter.
        :param terms: dictionary of terms to filter on. values should be lists.
        :param facet_fields: we need a proper comment on this TODO
        :param kwargs: any keyword args as per
            http://www.elasticsearch.org/guide/reference/api/search/uri-request.html
        :param notq: is this an "inverted" query - match all documents BUT the ones specified by the query
        '''
        conn, db = get_conn()
        if not q:
            ourq = pyes.query.MatchAllQuery()
        else:
            if flt:
                ourq = pyes.query.FuzzyLikeThisQuery(like_text=q,**kwargs)
            else:
                ourq = pyes.query.StringQuery(q, default_operator='AND')
        
        a,b,c=0,0,0
        a += 1
        print str(a) + '.'
        print terms
        if terms:
            for term in terms:
                b += 1
                print str(a) + '.' + str(b) + '.'
                print term
                for val in terms[term]:
                    c += 1
                    print str(a) + '.' + str(b) + '.' + str(c) + '.'+val
                    termq = pyes.query.TermQuery(term, val)
                    ourq = pyes.query.BoolQuery(must=[ourq,termq])
        
        # get an "inverted" or "negative" query - all hits BUT the ones found by the originally specified query
        # we can do this with BoolQuery apparently, but elasticsearch.org recommends a Not filter as faster, so that's what we'll try
        if notq:
            maq = pyes.query.MatchAllQuery() # the "all hits" bit
            # we can't use a NotFilter with a query, since that will only take another Filter
            # so we need a QueryFilter to make this abstract enough to handle any query ourq might be
            qf = pyes.filters.QueryFilter(ourq) # we wrap the original query in a QueryFilter...
            nf = pyes.filters.NotFilter(qf) # and can now use a fast NotFilter with it
            ourq = pyes.query.FilteredQuery(maq, nf) # replace the original query with our "inverted" one
        f = open ("debug.json", 'w')
        f.write(ourq.to_query_json())
        ourq = ourq.search(**kwargs)
        if facet_fields:
            for item in facet_fields:
                ourq.facet.add_term_facet(item['key'], size=item.get('size',100), order=item.get('order',"count"))
        out = conn.search(ourq, db, cls.__type__)
        return out

    @classmethod
    def raw_query(self, query_string):
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
    def query(cls, q='', terms=None, facet_fields=None, flt=False, notq=False, **kwargs):
        # TODO - check if that how you pass keyword arguments on to another function, EET
        # print kwargs
        
        # perhaps sometimes we WILL want all the unknowns, so we might want to write another method for that, or maybe *not* override query
        return DomainObject.query(q, {'name':['DOI']}, facet_fields, flt, notq=True, **kwargs)

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
