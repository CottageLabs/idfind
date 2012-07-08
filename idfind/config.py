import json
from sys import version_info as pyver

'''read the config.json file and make available as a config dict'''

def load_config(path):
    fileobj = open(path)
    c = ""
    for line in fileobj:
        if line.strip().startswith("#"):
            continue
        else:
            c += line
    out = json.loads(c)

    # add some critical defaults if necessary
    if 'facet_field' not in out:
        out['facet_field'] = ''
    
    # add dynamic pieces of information
    out['running_python_version'] = str(pyver.major) + '.' + str(pyver.minor) + '.' + str(pyver.micro) + '.' + str(pyver.releaselevel) + '.' + str(pyver.serial)

    return out

config = load_config('config.json')

__all__ = ['config']


''' wrap a config dict in a class if required'''

class Config(object):
    def __init__(self,confdict=config):
        '''Create Configuration object from a configuration dictionary.'''
        self.cfg = confdict
        
    def __getattr__(self, attr):
        return self.cfg.get(attr, None)
        


