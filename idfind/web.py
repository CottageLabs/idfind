from flask import Flask, jsonify, json, request, redirect, abort, make_response
from flask import render_template, flash
from flask.views import View, MethodView
from flaskext.login import login_user, current_user

import idfind.identifier
import idfind.dao
import idfind.iomanager
import idfind.importer
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
        # check the storage of identifiers, if already there, respond. else find it.
        identifier = idfind.dao.Identifier.query(q=q)
        if identifier['hits']['total'] != 0:
            flash('We already have that one!')
            return redirect('/identifier/'+q)

        ident = idfind.identifier.Identificator()
        answer = ident.identify(q)
        if answer:
            # save the identifier with its type, and add to the success rate of the test
            result = answer[0]
            #obj = idfind.dao.Test.get(answer[0]['id'])
            #obj['matches'] = obj.get('matches',0) + 1
            #obj.save()
            result['identifier'] = q
            idfind.dao.Identifier.upsert(result)
        else:
            idfind.dao.Identifier.upsert({"type":"unknown","identifier":q})
        if JSON:
            return outputJSON(results=answer)
        else:
            return render_template('answer.html',answer=answer,string=q)
    
    return render_template('identify.html')


@app.route('/parse', methods=['GET','POST'])
def parse():
    pass


class RateView(MethodView):
    # regex=ID of regex in system
    # score=8
    # e.g. a subjective assessment of the quality of the regex.
    def get(self):
        if not auth.collection.create(current_user, None):
            flash('You need to login to rate a regex')
            return redirect('/account/login')
        if request.values.get("type") is not None:
            return self.post()
        return render_template('rate.html')

    def post(self):
        if not auth.collection.create(current_user, None):
            abort(401)
        importer = idfind.importer.Importer(owner=current_user)
        importer.rate(request)
        flash('Successfully received your rating')
        return redirect('/account/%s/' % current_user.id)

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
            importer = idfind.importer.Importer(owner=current_user)
            importer.submit(request)
            flash('Successfully received %s' % request.values.get("test_or_desc"))
            return redirect('/')
        else:
            flash('You did not tell us if you are submitting a test or a description')
            return render_template('submit.html')

app.add_url_rule('/submit', view_func=SubmitView.as_view('submit'))


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


@app.route('/<path:path>')
def search(path=''):
    io = dosearch(path.replace(".json",""))
    if path.endswith(".json") or request.values.get('format',""):
        return outputJSON(results=io.results)
    else:
        return render_template('search/index.html', io=io)


# twitter
# some way of catching stuff sent to idfind via twitter, and returning it
# must be plenty of easy ways to check a twitter stream, then can just parse out the request details
# can build response out of the other sections


def dosearch(path,searchtype='identifier'):
    args = {}
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

