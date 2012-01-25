#https://api.twitter.com/1/statuses/mentions.json?include_entities=true
#https://dev.twitter.com/docs/auth/oauth

'''this tracks tweets on twitter and when one comes in with a string to identify,
it tries to identify it and passes back the result as a tweet'''

import twitter
import re
import whatid.dao
import whatid.identifier

class TweetListen(object):
    api = None
    homeurl = 'http://localhost:5001/'
    regexstr = '@emanuil_twitdev (.+)'
    def __init__(self):
        credentials = whatid.dao.TwitterCredentials.query(q='*')
        
        self.api = twitter.Api(
        consumer_key = credentials['hits']['hits'][0]['_source']['consumer_key'],
        consumer_secret = credentials['hits']['hits'][0]['_source']['consumer_secret'],
        access_token_key = credentials['hits']['hits'][0]['_source']['access_token_key'],
        access_token_secret = credentials['hits']['hits'][0]['_source']['access_token_secret']
        )
    
    def listen(self):
        regex = re.compile(self.regexstr, re.IGNORECASE)
        i = 0 # debugging only
        
        while True:
            mentions = self.api.GetMentions()
            
            for status in mentions:
                i += 1
                match = regex.search(status.text)
                
                if match:
                    q = match.group(1)
                    print q
                    # check the storage of identifiers, if already there, respond. else find it.
                    identifier = whatid.dao.Identifier.query(q=q)
                    if identifier['hits']['total'] != 0:
                        self.api.PostUpdate('@' + status.user.screen_name + ' ' + self.homeurl + 'identifier/' + q, in_reply_to_status_id = status.id)
                        
                        print str(i)+ ' ' + status.text + ' Got it! From the storage.'
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
                        
                        tweetreply = '@' + status.user.screen_name + ' '
                        
                        if result['url_prefix']:
                            tweetreply += result['url_prefix']
                            tweetreply += q
                            # We can't have a URL Suffix ONLY, can we?
                            if result['url_suffix']:
                                tweetreply += result['url_suffix']
                            tweetreply += ' '
                        
                        tweetreply += self.homeurl + 'identifier/' + q
                        
                        self.api.PostUpdate(tweetreply, in_reply_to_status_id = status.id)
                        
                        print str(i)+ ' ' + status.text + ' Got it! Engine ident.'
                        continue
                        
                    else:
                        whatid.dao.Identifier.upsert({"type":"unknown","identifier":q})
                        self.api.PostUpdate('@' + status.user.screen_name + ' Unknown identifier.', in_reply_to_status_id = status.id)
                        
                        print str(i)+ ' ' + status.text + ' Unknown identifier.'
                        continue
                        
                else:
                    print str(i)+ ' ' + status.text + 'No matches.'
            
            sleep(60) # seconds

x = TweetListen()
x.listen()