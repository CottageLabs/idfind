import urllib2
from copy import deepcopy
import whatid.dao

class IOManager(object):
    def __init__(self, results, args={}, path=""):
        self.results = results
        self.args = args
        self.path = path

    def get_q(self):
        return self.args.get('q','')
    
    def get_path_params(self,myargs):
        param = '/' + self.path + '?' if (self.path != '') else self.config.base_url + '?'
        if 'q' in myargs:
            param += 'q=' + myargs['q'] + '&'
        if self.showkeys:
            param += 'showkeys=' + self.showkeys + '&'
        return param

    def get_result_display(self,counter):
        '''use the result_display object as a template for search results'''
        display = self.config.result_display
        output = ""
        if not display:
            return output

        for item in display:
            line = ""
            for pobj in item:
                if 'key' in pobj:
                    keydisp = self.get_str(self.set()[counter],pobj['key'])
                    if keydisp:
                        try:
                            keydisp = unichr(keydisp)
                        except:
                            pass
                        line += pobj.get('pre','') + keydisp + pobj.get('post','') + " "
                if 'default' in pobj:
                    line += pobj.get('default','') + " "
            if line:
                output += line.strip().strip(",") + "<br />"

        if self.get_showkeys():
            output += '<table>'
            keys = [i for i in self.get_showkeys().split(',')]
            for key in keys:
                out = self.get_str(self.set()[counter],key)
                if out:
                    output += '<tr><td><strong>' + key + '</strong>: ' + out + '</td></tr>'
            output += '</table>'
        return output
        
    '''get all currently available keys in ES'''
    def get_keys(self,rectype='Regex'):
        if rectype == 'Record':
            res = bibserver.dao.Record.get_mapping()
            which = 'record'
        elif rectype == 'Collection':
            res = bibserver.dao.Collection.get_mapping()
            which = 'collection'
        keys = [str(i) for i in res[which]['properties'].keys()]
        keys.sort()
        return keys
    
    '''get keys to show on results'''
    def get_showkeys(self,format="string"):
        if format == "string":
            if not self.showkeys:
                return "";
            return self.showkeys
        else:
            if not self.showkeys:
                return []
            return [i for i in self.showkeys.split(',')]

    def get_facet_fields(self):
        return [i['key'] for i in self.config.facet_fields]

    def get_rpp_options(self):
        return self.config.results_per_page_options

    def get_sort_fields(self, rectype='Record'):
        fields = self.get_keys(rectype)
        sortfields = []
        for item in fields:
            try:
                if rectype == 'Record':
                    bibserver.dao.Record.query(sort={item+self.config.facet_field: {"order":"asc"}})
                elif rectype == 'Collection':
                    bibserver.dao.Collection.query(sort={item: {"order":"asc"}})
                sortfields.append(item)
            except:
                pass
        sortfields.sort()
        return sortfields

    def numFound(self):
        return int(self.results['hits']['total'])

    def page_size(self):
        return int(self.args.get("size",10))

    def paging_range(self):
        return ( self.numFound() / self.page_size() ) + 1

    def sorted_by(self):
        if "sort" in self.args:
            return self.args["sort"].keys()[0].replace(self.config.facet_field,"")
        return ""

    def sort_order(self):
        if "sort" in self.args:
            return self.args["sort"][self.args["sort"].keys()[0]]["order"]
        return ""
        
    def start(self):
        return int(self.args.get('start',0))

    def set(self):
        '''Return list of search result items'''
        return [rec['_source'] for rec in self.results['hits']['hits']]


    def get_str(self, result, field, raw=False):
        res = result.get(field,"")
        if not res:
            return ""
        if isinstance(res,list):
            return ','.join(res)
        else:
            return res

        
    def get_record_as_table(self):
        return self.tablify(self.set()[0])
        
    def tablify(self,thing):
        if not thing:
            return ""
        try:
            s = '<table>'
            for key,val in thing.iteritems():
                s += '<tr><td><strong>' + key + '</strong></td><td>' + self.tablify(val) + '</td></tr>'
            s += '</table>'
        except:
            if isinstance(thing,list):
                s = '<table>'
                for item in thing:
                    s += '<tr><td>' + self.tablify(item) + '</tr></td>'
                s += '</table>'
            else:
                s = thing
        return s


