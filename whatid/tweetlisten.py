#https://api.twitter.com/1/statuses/mentions.json?include_entities=true
#https://dev.twitter.com/docs/auth/oauth

'''this tracks tweets on twitter and when one comes in with a string to identify,
it tries to identify it and passes back the result as a tweet'''

import twitter
import re
from time import sleep
import whatid.dao
import whatid.identifier
from whatid.config import config

class TweetListen(object):
    api = None
    homeurl = config['TWEETLISTEN_BASE_URL']
    check_for = '@' + config['twitter_account'] + ' (.+)'
    
    def __init__(self):
        credentials = whatid.dao.TwitterCreds.query(q='*')
        
        if credentials['hits']['total'] != 0:
            self.api = twitter.Api(
            consumer_key = credentials['hits']['hits'][0]['_source']['consumer_key'],
            consumer_secret = credentials['hits']['hits'][0]['_source']['consumer_secret'],
            access_token_key = credentials['hits']['hits'][0]['_source']['access_token_key'],
            access_token_secret = credentials['hits']['hits'][0]['_source']['access_token_secret']
            )
        else:
            raise Exception('Oops, you need to index the twitter credentials into elasticsearch first!')

    def save_lastid(self, last_proc_tweet):
        
        upsertthis = {
            "last_mention_id":last_proc_tweet,
            "id":1
            }
        
        whatid.dao.TwitterLastID.upsert(upsertthis)
        
    def get_lastid(self):
        ids = whatid.dao.TwitterLastID.query(q='*')
            
        lm = None
        
        if ids['hits']['total'] != 0:
            lm = ids['hits']['hits'][0]['_source']['last_mention_id']
        
        return lm
        
    def listen(self):
        regex = re.compile(self.check_for, re.IGNORECASE)
        
        while True:
            
            lm = self.get_lastid() # we are interested in the "last_mention_id" field of the ES hit, so that we can use it to request only the tweets we need below
            
            if lm:
                mentions = self.api.GetMentions(since_id = lm)
            else:
                mentions = self.api.GetMentions()
            
            mentions.reverse()
            
            for status in mentions:
                # print status.created_at + '  ' + str(status.id) + '  ' + status.user.screen_name + '  ' + status.text # uncomment to see info about every tweet which is being processed
                try:
                    match = regex.search(status.text)
                    
                    if match:
                        q = match.group(1)
                        
                        print q # debug
                        
                        tweetreply = '@' + status.user.screen_name + ' ' # can't construct the whole string and then PostUpdate() it to Twitter at the end of the processing loop - that loop uses 'continue' in order to prevent further processing when one of the cases is hit... 
                        # yeah, it's ugly, the original code in whatid.web.identify uses an HTTP redirect and thus stops further execution, but we can't do that here, hence the continue
                    
                        # check the storage of identifiers, if already there, respond. else find it.
                        identifier = whatid.dao.Identifier.query(q=q)
                        if identifier['hits']['total'] != 0:
                            
                            tweetreply += self.homeurl + 'identifier/' + q
                            self.save_lastid(status.id) # create/replace the ES document containing the last-processed tweet id
                            self.api.PostUpdate(tweetreply, in_reply_to_status_id = status.id)
                            
                            
                            print status.text + ' Got it! From the storage.'
                            continue

                        ident = whatid.identifier.Identificator()
                        answer = ident.identify(q)
                        if answer:
                            # save the identifier with its type, and add to the success rate of the test
                            result = answer[0]
                            #obj = whatid.dao.Test.get(answer[0]['id'])
                            #obj['matches'] = obj.get('matches',0) + 1
                            #obj.save()
                            result['identifier'] = q
                            whatid.dao.Identifier.upsert(result)
                            
                            if result['url_prefix']:
                                tweetreply += result['url_prefix']
                                tweetreply += q
                                # We can't have a URL Suffix ONLY, can we?
                                if result['url_suffix']:
                                    tweetreply += result['url_suffix']
                                tweetreply += ' '
                                
                            tweetreply += self.homeurl + 'identifier/' + q
                            
                            self.save_lastid(status.id) # create/replace the ES document containing the last-processed tweet id
                            self.api.PostUpdate(tweetreply, in_reply_to_status_id = status.id)
                            
                            
                            print status.text + ' Got it! Engine ident.'
                            continue
                            
                        else:
                            whatid.dao.Identifier.upsert({"type":"unknown","identifier":q})
                            
                            tweetreply += 'Unknown identifier.'
                            self.save_lastid(status.id) # create/replace the ES document containing the last-processed tweet id
                            self.api.PostUpdate(tweetreply, in_reply_to_status_id = status.id)
                            
                            
                            print status.text + ' Unknown identifier.'
                            continue
                            
                    else:
                        print str(status.id) + ' ' + status.text + 'This tweet doesn\'t match the format (regex): ' + self.check_for
                    

                except twitter.TwitterError as error:
                    print 'Twitter error while processing tweet (id = ' + str(status.id) + ' ); Error was: ' + error.args[0]
                    print
                    
            sleep(61) # sleep a minute - make sure we are not getting cached responses from the python-twitter library

x = TweetListen()
x.listen()