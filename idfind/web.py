import re
import json

from flask import Flask, jsonify, json, request, redirect, abort, make_response
from flask import render_template, flash
from flask.views import View, MethodView
from flask.ext.login import login_user, current_user

import idfind.identifier
import idfind.dao
import idfind.iomanager
import idfind.importer
from idfind.config import config
from idfind.core import app, login_manager
from idfind.view.account import blueprint as account
from idfind import auth

app.register_blueprint(account, url_prefix='/account')


# NB: the decorator appears to kill the function for normal usage
@login_manager.user_loader
def load_account_for_login_manager(userid):
    out = idfind.dao.Account.get(userid)
    return out

@app.context_processor
def set_current_user():
    """ Set some template context globals. """
    return dict(current_user=current_user)

@app.before_request
def standard_authentication():
    """Check remote_user on a per-request basis."""
    remote_user = request.headers.get('REMOTE_USER', '')
    if remote_user:
        user = idfind.dao.Account.get(remote_user)
        if user:
            login_user(user, remember=False)
    # add a check for provision of api key
    elif 'api_key' in request.values:
        res = idfind.dao.Account.query(q='api_key:"' + request.values['api_key'] + '"')['hits']['hits']
        if len(res) == 1:
            user = idfind.dao.Account.get(res[0]['_source']['id'])
            if user:
                login_user(user, remember=False)


@app.template_filter('dtformat')
def datetimeformat(value, format='%d-%B-%Y %H:%M:%S'):
    return value#.strftime(format)
                
@app.route('/')
def home():
    return render_template('home/index.html')

@app.route('/account/<user>')
def account(user):
    if hasattr(current_user,'id'):
        if user == current_user.id:
            return render_template('account/view.html',current_user=current_user)
    flash('You are not that user. Or you are not logged in.')
    return redirect('/account/login')


@app.route('/content/<path:path>')
def content(path):
    return render_template('home/content.html', page=path)


#@app.route('/test')
#@app.route('/test/<rid>')
def regex(rid=None):
    JSON = False
    if rid.endswith(".json") or request.values.get('format',"") == "json":
        rid = rid.replace(".json","")
        JSON = True

    if rid:
        # get the regex to which the rid points
        pass
    else:
        # get the search page of the regex collection
        pass
        
    if res["hits"]["total"] == 0:
        abort(404)
    elif JSON:
        return outputJSON(results=res, coll=cid, record=True)
    else:
        io = idfind.iomanager.IOManager(res)
        return render_template('test.html', io=io)


#@app.route('/identifier')
#@app.route('/identifier/<iid>')
def identifier(iid=None):
    JSON = False
    if iid.endswith(".json") or request.values.get('format',"") == "json":
        iid = iid.replace(".json","")
        JSON = True

    if iid:
        # get the identifier to which the rid points
        pass
    else:
        # get the search page of the regex collection
        pass
        
    if res["hits"]["total"] == 0:
        abort(404)
    elif JSON:
        return outputJSON(results=res, coll=cid, record=True)
    else:
        io = idfind.iomanager.IOManager(res)
        return render_template('identifier.html', io=io)


#@app.route('/description')
#@app.route('/description/<iid>')
def description(did=None):
    JSON = False
    if did.endswith(".json") or request.values.get('format',"") == "json":
        did = did.replace(".json","")
        JSON = True

    if did:
        # get the identifier to which the rid points
        pass
    else:
        # get the search page of the regex collection
        pass
        
    if res["hits"]["total"] == 0:
        abort(404)
    elif JSON:
        return outputJSON(results=res, coll=cid, record=True)
    else:
        io = idfind.iomanager.IOManager(res)
        return render_template('description.html', io=io)

@app.route('/identify', methods=['GET','POST'])
@app.route('/identify/<therest>', methods=['GET','POST'])
def identify(therest=''):
    JSON = False
    
    if therest:
        q = therest
    else:
        q = request.values.get('q','').strip('"')
    
    if q.endswith(".json") or request.values.get('format',"") == "json":
            JSON = True
            q = q.rstrip('.json')
            
    if q:
        answers = idfind.dao.Identifier.identify(q=q)
        
        if JSON:
            return outputJSON(results=answers)
        else:
            tests_used = []
            for a in answers:
                # TODO: perhaps build up a query to get all the successful
                # tests instead of getting them one by one, separate queries
                t = idfind.dao.Test.query(q=a['name'])
                if t['hits']['total'] != 0:
                    t = t['hits']['hits']
                    for hit in t:
                    # TODO: ask elasticsearch for an exact match on the test
                    # name in the query line above - the below is really dumb!
                    # Or, of course, just implement the TODO above, get rid of this completely...
                        if hit['_source']['name'] == a['name']:
                            tests_used.append(hit)
             
            return render_template('answer.html',answer=answers, identifier_string=q, tests=tests_used)
    
    return render_template('identify.html')


    
@app.route('/browse', methods=['GET'])
def browse():
    # tests = idfind.dao.Test.query(sort=[{"name":"asc"}]) # get all the tests # ES query with sorting fails for tests which have spaces in their names
    tests = idfind.dao.Test.query() # get all the tests
    tests = tests['hits']['hits']
    
    descs = idfind.dao.Description.query() # get all the descriptions
    descs = descs['hits']['hits']
    
    return render_template('browse.html', things=tests+descs)


@app.route('/parse', methods=['GET','POST'])
def parse():
    pass


class RateView(MethodView):
    def get(self):
        if not auth.collection.create(current_user, None):
            flash('You need to login to rate a regex')
            return redirect('/account/login')
        if request.values.get("test_worked") is not None:
            return self.post()
            
        tests = idfind.dao.Test.query() # get all the tests
        tests = tests['hits']['hits']

        return render_template('rate.html', tests=tests)

    def post(self):
        if not auth.collection.create(current_user, None):
            abort(401)
        importer = idfind.importer.Importer(owner=current_user)
        importer.rate(request)
        flash('Successfully received your rating')
        return redirect('/')

app.add_url_rule('/rate', view_func=RateView.as_view('rate'))


class SubmitView(MethodView):
    '''Submit a regex or an identifier for addition to the collections. In the format as specified in the collections.
    Perhaps also submit additional actions for a particular identifier.
    Should trigger email alert to mailing list for a simple approval workflow'''
    def get(self):
        if not auth.collection.create(current_user, None):
            flash('You need to login to be able to submit.')
            return redirect('/account/login')
        if request.values.get("test_or_desc") is not None:
            return self.post()
        return render_template('submit.html')

    def post(self):
        if not auth.collection.create(current_user, None):
            abort(401)
        # TODO: need some better validation. see python flask docs for info.
        if 'test_or_desc' in request.values:
            if request.values['test_or_desc'] == 'test':
                if request.values['regex']:
                    try:
                        dummy = re.compile(request.values['regex'])
                    except re.error as e:
                        flash('There is a problem with the regular expression you have provided. Python needs to be able to understand it. Our Python (' + config['running_python_version'] + ') says: ' + e.message)
                        return render_template('submit.html')
                else:
                    flash('You need to provide a regular expression when you\'re submitting a Test')
                    return render_template('submit.html')
            
            if request.values['name']:
                importer = idfind.importer.Importer(owner=current_user)
                importer.submit(request)
                flash('Successfully received %s' % request.values["test_or_desc"])
                return redirect('/browse#' + request.values['name'])
            else:
                flash('We need a name for your test / description')
                return render_template('submit.html')
        else:
            flash('You did not tell us if you are submitting a test or a description')
            return render_template('submit.html')

app.add_url_rule('/submit', view_func=SubmitView.as_view('submit'))


# code from bibserver - need to review what it does and why, and see if it works
@app.route('/record/<path:path>')
def record(path):
    JSON = False
    if path.endswith(".json") or request.values.get('format',"") == "json":
        path = path.replace(".json","")
        JSON = True

    res = idfind.dao.Test.query(q='id:"' + path + '"')

    if res["hits"]["total"] == 0:
        abort(404)
    elif JSON:
        return outputJSON(results=res, coll=cid, record=True)
    elif res["hits"]["total"] != 1:
        io = idfind.iomanager.IOManager(res)
        return render_template('record.html', io=io, multiple=True)
    else:
        io = idfind.iomanager.IOManager(res)
        return render_template('record.html', io=io)

# code from bibserver - need to review what it does and why, and see if it works
@app.route('/<path:path>')
def search(path=''):
    io = dosearch(path.replace(".json",""))
    if path.endswith(".json") or request.values.get('format',""):
        return outputJSON(results=io.results)
    else:
        return render_template('search/index.html', io=io)


# code from bibserver - need to review what it does and why, and see if it works
def dosearch(path,searchtype='identifier'):
    # prevent UnboundLocalError: local variable X referenced before assignment errors by initialising some variables
    args = {}
    implicit_key = None
    
    if 'from' in request.values:
        args['start'] = request.values.get('from')
    if 'size' in request.values:
        args['size'] = request.values.get('size')
    if 'sort' in request.values:
        if request.values.get("sort") != "..." and request.values.get("sort") != "":
            args['sort'] = {request.values.get('sort') : {"order" : request.values.get('order','asc')}}
    if 'q' in request.values:
        if len(request.values.get('q')) > 0:
            args['q'] = request.values.get('q')

    if path != '' and not path.startswith("search"):
        path = path.strip()
        if path.endswith("/"):
            path = path[:-1]
        bits = path.split('/',1)
        if len(bits) == 2:
            implicit_key = bits[0]
            implicit_value = bits[1]

    if implicit_key:
        args['q'] = implicit_value

    if searchtype == 'identifier' or implicit_key == 'identifier':
        results = idfind.dao.Identifier.query(**args)
    if searchtype == 'test' or implicit_key == 'test':
        results = idfind.dao.Test.query(**args)
    if searchtype == 'description' or implicit_key == 'description':
        results = idfind.dao.Description.query(**args)
    return idfind.iomanager.IOManager(results, args)


def outputJSON(results, record=False):
    '''build a JSON response, with metadata unless specifically asked to suppress'''
    # TODO: in some circumstances, people data should be added to collections too.
    out = {"metadata":{}}
    out['metadata']['query'] = request.base_url + '?' + request.query_string
    out['records'] = results
    out['metadata']['from'] = request.values.get('from',0)
    out['metadata']['size'] = request.values.get('size',10)

    resp = make_response( json.dumps(out, sort_keys=True, indent=4) )
    resp.mimetype = "application/json"
    return resp

if __name__ == "__main__":
    idfind.dao.init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)

