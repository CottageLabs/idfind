from flask import Flask, jsonify, json, request, redirect, abort, make_response
from flask import render_template, flash
from flask.views import View, MethodView
from flaskext.login import login_user, current_user

import whatid.identifier
import whatid.dao
import whatid.iomanager
import whatid.importer
from whatid.core import app, login_manager
from whatid.view.account import blueprint as account
from whatid import auth

app.register_blueprint(account, url_prefix='/account')


# NB: the decorator appears to kill the function for normal usage
@login_manager.user_loader
def load_account_for_login_manager(userid):
    out = whatid.dao.Account.get(userid)
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
        user = whatid.dao.Account.get(remote_user)
        if user:
            login_user(user, remember=False)
    # add a check for provision of api key
    elif 'api_key' in request.values:
        res = whatid.dao.Account.query(q='api_key:"' + request.values['api_key'] + '"')['hits']['hits']
        if len(res) == 1:
            user = whatid.dao.Account.get(res[0]['_source']['id'])
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


@app.route('/regex')
@app.route('/regex/<rid>')
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
        io = whatid.iomanager.IOManager(res)
        return render_template('regex.html', io=io)


@app.route('/identifier')
@app.route('/identifier/<iid>')
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
        io = whatid.iomanager.IOManager(res)
        return render_template('identifier.html', io=io)


@app.route('/identify', methods=['GET','POST'])
def identify():
    # string=10.1007/12345678..
    #[
    #  {
    #    "string":"10.1007/12345678..",
    #    "type":"doi",
    #    "confidence":"1.0",
    #    "actions":[...]
    #  },
    #  ...
    #]
    if request.method == "GET":
        return render_template('identify.html')

    if request.method == "POST":
        string = request.values.get('string','')
        if string:
            identifier = whatid.identifier.Identificator()
            answer = identifier.identify(string)
            return render_template('answer.html',answer=answer,string=string)
        return render_template('identify.html')


@app.route('/parse', methods=['GET','POST'])
def parse():
    # string="stuff that may have identifier in it"
    #[
    #  {
    #    "string":"blah",
    #    "type":"doi",
    #    "confidence":"1.0",
    #    "actions":[...]
    #  },
    #  ...
    #]
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
        importer = whatid.importer.Importer(owner=current_user)
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
        if request.values.get("type") is not None:
            return self.post()
        return render_template('submit.html')

    def post(self):
        if not auth.collection.create(current_user, None):
            abort(401)
        if 'type' in request.values:
            importer = whatid.importer.Importer(owner=current_user)
            importer.submit(request)
            flash('Successfully received %s' % request.values.get("type"))
            return redirect('/')
        else:
            flash('You did not provide a type - regex or identifier')
            return render_template('submit.html')

app.add_url_rule('/submit', view_func=SubmitView.as_view('submit'))


# twitter
# some way of catching stuff sent to whatid via twitter, and returning it
# must be plenty of easy ways to check a twitter stream, then can just parse out the request details
# can build response out of the other sections


def dosearch(path,searchtype='Regex'):
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

    if searchtype == 'Record':
        results = whatid.dao.Record.query(**args)
    else:
        results = whatid.dao.Collection.query(**args)
    return whatid.iomanager.IOManager(results, args, facet_fields, showkeys, incollection, implicit_key, implicit_value, path)


def outputJSON(results, record=False):
    '''build a JSON response, with metadata unless specifically asked to suppress'''
    # TODO: in some circumstances, people data should be added to collections too.
    out = {"metadata":{}}
    out['metadata']['query'] = request.base_url + '?' + request.query_string
    out['records'] = [i['_source'] for i in results['hits']['hits']]
    if request.values.get('facets','') and results['facets']:
        out['facets'] = results['facets']
    out['metadata']['from'] = request.values.get('from',0)
    out['metadata']['size'] = request.values.get('size',10)

    resp = make_response( json.dumps(out, sort_keys=True, indent=4) )
    resp.mimetype = "application/json"
    return resp

if __name__ == "__main__":
    whatid.dao.init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)

