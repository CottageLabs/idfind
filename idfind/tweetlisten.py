#https://api.twitter.com/1/statuses/mentions.json?include_entities=true
#https://dev.twitter.com/docs/auth/oauth

'''this tracks tweets on twitter and when one comes in with a string to identify,
it tries to identify it and passes back the result as a tweet'''

import twitter
import re
from time import sleep
import idfind.dao
import idfind.identifier
from idfind.config import config

class TweetListen(object):
    api = None
    homeurl = config['TWEETLISTEN_BASE_URL']
    check_for = None # string to be used as regex later: @account_name, where the twitter username is whatever our twitter account is called
    
    def __init__(self):
        credentials = idfind.dao.TwitterCreds.query(q='*')
        
        if credentials['hits']['total'] != 0:
            self.api = twitter.Api(
            consumer_key = credentials['hits']['hits'][0]['_source']['consumer_key'],
            consumer_secret = credentials['hits']['hits'][0]['_source']['consumer_secret'],
            access_token_key = credentials['hits']['hits'][0]['_source']['access_token_key'],
            access_token_secret = credentials['hits']['hits'][0]['_source']['access_token_secret']
            )
            
            user = self.api.VerifyCredentials()
            
            if user:
                name = user.GetScreenName()
                self.check_for = '@' + name + ' (.+)'
            else:
                raise Exception('Oops, invalid twitter credentials!')
                
        else:
            raise Exception('Oops, you need to index the twitter credentials into elasticsearch first!')

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
        
    def listen(self):
        regex = re.compile(self.check_for, re.IGNORECASE)
        
        while True:
            
            lm = self.get_lastid()
            
            if lm:
                mentions = self.api.GetMentions(since_id = lm)
            else:
                mentions = self.api.GetMentions()
            
            mentions.reverse()
            
            for status in mentions:
                # uncomment to see info about every tweet which is being processed
                # print status.created_at + '  ' + str(status.id) + '  ' + status.user.screen_name + '  ' + status.text 
                try:
                    match = regex.search(status.text)
                    
                    if match:
                        q = match.group(1)
                        
                        # print q # debug
                        
                        tweetreply = '@' + status.user.screen_name + ' '
                        
                        answer = idfind.dao.Identifier.identify(q=q)
                        
                        if answer:
                        # we've got this identifier
                            result = answer[0]
                            
                            if result['url_prefix']:
                                tweetreply += result['url_prefix']
                                tweetreply += q
                                # We can't have a URL Suffix WITHOUT a URL Prefix, can we?
                                if result['url_suffix']:
                                    tweetreply += result['url_suffix']
                                tweetreply += '; '
                                
                            tweetreply += 'info @ ' + self.homeurl + '/identify/' + q
                            
                            debug_prefix = 'Got it'
                        else:
                        # unknown identifier
                            tweetreply += 'Unknown identifier.'
                            debug_prefix = 'Unknown identifier'
                            
                        print debug_prefix + ' ::: Tweet ID: ' + str(status.id) + ', Text: "' + status.text + '"' + ', Asker: ' + status.GetUser().GetScreenName()
                            
                        self.save_lastid(status.id) # create/replace the ES document containing the last-processed tweet id
                        self.api.PostUpdate(tweetreply, in_reply_to_status_id = status.id)
                      
                    else:
                        print str(status.id) + ' ' + status.text + 'This tweet doesn\'t match the regex with the project\'s username: ' + self.check_for
                    

                except twitter.TwitterError as error:
                    print 'Twitter error while processing tweet (id = ' + str(status.id) + ' ); Error was: ' + error.args[0]
                    
            sleep(61) # sleep a minute - make sure we are not getting cached responses from the python-twitter library
        
x = TweetListen()
x.listen()