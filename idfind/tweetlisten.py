#https://api.twitter.com/1/statuses/mentions.json?include_entities=true
#https://dev.twitter.com/docs/auth/oauth

'''this tracks tweets on twitter and when one comes in with a string to identify,
it tries to identify it and passes back the result as a tweet'''

import twitter
import json
import re
import logging
import sys
from time import sleep
import requests
from urllib2 import URLError

from flask import url_for

import idfind.dao
import idfind.identifier
from idfind.config import config

requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

LOG_FORMAT = '%(asctime)-15s :: %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
log = logging.getLogger(__name__)

class TweetListen(object):
    api = None
    homeurl = config['TWEETLISTEN_BASE_URL']
    check_for = None # string to be used as regex later: @account_name, where the twitter username is whatever our twitter account is called
    
    def __init__(self):
        credentials = self.get_twitter_creds()
        
        if credentials:
            self.api = twitter.Twitter(
                auth=twitter.OAuth(
                    credentials['oauth_token'],
                    credentials['oauth_secret'],
                    credentials['consumer_key'],
                    credentials['consumer_secret']
                )
            )

           
            user = self.api.account.verify_credentials()

            if user:
                name = user['screen_name']
                self.check_for = '@' + name + ' (.+)'
            else:
                fail('Oops, invalid twitter credentials')
                
        else:
            fail(
            '''Oops, you need to put the twitter credentials into {0}
first! The twitter service is looking for a JSON dictionary with
"consumer_key", "consumer_secret", "access_token_key" and
"access_token_secret" defined. You can get these by logging into
https://dev.twitter.com as the idfind user. Ask the maintainer of this
package for the password.'''.format(config['TWITTER_CREDENTIALS_FILE'])
            )

        idfind.dao.init_db() # create the idfind index if it doesn't exist already

    @classmethod
    def get_twitter_creds(cls):
        with open(config['TWITTER_CREDENTIALS_FILE'], 'rb') as f:
            credentials = json.loads(f.read())
        return credentials

    def save_lastid(self, last_proc_tweet):
        
        upsertthis = {
            "last_mention_id":last_proc_tweet,
            "id":1
            }
        
        idfind.dao.TwitterLastID.upsert(upsertthis)
        
    def get_lastid(self):
        ids = idfind.dao.TwitterLastID.query(q='*')
            
        lm = None
        
        if ids['hits']['total'] != 0:
            lm = ids['hits']['hits'][0]['_source']['last_mention_id']
        
        return lm

    def sturdy_listen(self):
        '''Listen to tweet mentions, but don't balk on network errors
        (just log them).'''

        while True:
            try:
                self.listen()
            except URLError:
                log.warn('Network problem. Nvm, hopefully it will work later.')
        
    def listen(self):
        regex = re.compile(self.check_for, re.IGNORECASE)
        
        while True:
            
            lm = self.get_lastid()
            
            if lm:
                mentions = self.api.statuses.mentions_timeline(since_id=lm)
            else:
                mentions = self.api.statuses.mentions_timeline()
            
            mentions.reverse()
            
            for status in mentions:
                try:
                    match = regex.search(status['text'])
                    
                    if match:
                        q = match.group(1)
                        
                        log.debug(q)
                        
                        tweetreply = '@' + status['user']['screen_name'] + ' '
                        
                        answer = idfind.dao.Identifier.identify(q=q)
                        
                        if answer:
                        # we've got this identifier
                            result = answer[0]

                            tweetreply += result['name'] + ' -> '
                            
                            if result['url_prefix']:
                                tweetreply += result['url_prefix']
                                tweetreply += q
                                if result['url_suffix']:
                                    tweetreply += result['url_suffix']
                                tweetreply += '; '
                                
                            tweetreply += 'info @ ' + self.homeurl + '/identify' + '/' + q
                            
                            debug_prefix = 'Got it'
                        else:
                        # unknown identifier
                            tweetreply += 'Unknown identifier.'
                            debug_prefix = 'Unknown identifier'
                            
                        log.info('{debug} == Time: {status[created_at]}, ID: {status[id_str]}, Asker: {status[user][screen_name]}, Text: {status[text]}'.format(debug=debug_prefix, status=status))
                            
                        self.save_lastid(status['id']) # create/replace the ES document containing the last-processed tweet id
                        self.api.statuses.update(status=tweetreply, in_reply_to_status_id=status['id'])
                      
                    else:
                        log.warn(str(status['id']) + ' ' + status['text'] + 'This tweet doesn\'t match the regex with the project\'s username: ' + self.check_for)
                    

                except twitter.TwitterError as error:
                    log.error('Twitter error while processing tweet (id = ' + str(status['id']) + ' ); Error was: ' + str(error))
                    
            sleep(61) # sleep a minute - make sure we are not getting cached responses from the python-twitter library

def fail(msg):
    log.critical(msg)
    raise Exception(msg)

def main(argv=None):

    if not argv:
        argv = sys.argv

    x = TweetListen()
    x.sturdy_listen()


if __name__ == '__main__':
    main()
