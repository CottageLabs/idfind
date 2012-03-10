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
    check_for = '@' + config['twitter_account'] + ' (.+)'
    
    def __init__(self):
        credentials = idfind.dao.TwitterCreds.query(q='*')
        
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
                        
                        tweetreply = '@' + status.user.screen_name + ' ' # can't construct the whole string and then PostUpdate() it to Twitter at the end of the processing loop - that loop uses 'continue' in order to prevent further processing when one of the cases is hit... 
                        # yeah, it's ugly, the original code in idfind.web.identify uses an HTTP redirect and thus stops further execution, but we can't do that here, hence the continue
                    
                        # check the storage of identifiers, if already there, respond. else find it.
                        identifier = idfind.dao.Identifier.query(q=q)
                        if identifier['hits']['total'] != 0:
                            
                            identifier_record = identifier['hits']['hits'][0]['_source']
                            
                            url_prefix = None
                            url_suffix = None
                            if 'url_prefix' in identifier_record:
                                url_prefix = identifier_record['url_prefix']
                            if 'url_suffix' in identifier_record:
                                url_suffix = identifier_record['url_suffix']
                            
                            if url_prefix:
                                tweetreply += url_prefix
                                tweetreply += q
                                # We can't have a URL Suffix ONLY, can we?
                                if url_suffix:
                                    tweetreply += url_suffix
                                tweetreply += '; '
                            
                            tweetreply += 'info @ ' + self.homeurl + '/identifier/' + q
                            self.save_lastid(status.id) # create/replace the ES document containing the last-processed tweet id
                            self.api.PostUpdate(tweetreply, in_reply_to_status_id = status.id)
                            
                            
                            print 'Got it! From the storage :: ' + str(status.id) + ' "' + status.text + '"'
                            continue

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
                            
                            if result['url_prefix']:
                                tweetreply += result['url_prefix']
                                tweetreply += q
                                # We can't have a URL Suffix ONLY, can we?
                                if result['url_suffix']:
                                    tweetreply += result['url_suffix']
                                tweetreply += '; '
                                
                            tweetreply += 'info @ ' + self.homeurl + '/identifier/' + q
                            
                            self.save_lastid(status.id) # create/replace the ES document containing the last-processed tweet id
                            self.api.PostUpdate(tweetreply, in_reply_to_status_id = status.id)
                            
                            
                            print 'Got it! Engine ident :: ' + str(status.id) + ' "' + status.text + '"'
                            continue
                            
                        else:
                            idfind.dao.UIdentifier.upsert({"identifier":q, "id":q}) # prevent duplicates in the unknowns
                            
                            tweetreply += 'Unknown identifier.'
                            self.save_lastid(status.id) # create/replace the ES document containing the last-processed tweet id
                            self.api.PostUpdate(tweetreply, in_reply_to_status_id = status.id)
                            
                            
                            print 'Unknown identifier :: ' + str(status.id) + ' "' + status.text + '"'
                            continue
                            
                    else:
                        print str(status.id) + ' ' + status.text + 'This tweet doesn\'t match the format (regex): ' + self.check_for
                    

                except twitter.TwitterError as error:
                    print 'Twitter error while processing tweet (id = ' + str(status.id) + ' ); Error was: ' + error.args[0]
                    print
                    
            sleep(61) # sleep a minute - make sure we are not getting cached responses from the python-twitter library

x = TweetListen()
x.listen()
