'''this tracks tweets on twitter and when one comes in with a string to identify,
it tries to identify it and passes back the result as a tweet'''

import twitter
import whatid.dao

class TweetListen(object):
    def __init__(self):
        # EET: need to learn how to query ES once and for all from code - just index/type and also  index/type/name:value pairs. Get the twitter credentials from the ES index and use them to connect, then continue development: we need to parse mentions (and perhaps DMs?) as per issue #1 on GitHub
        #credentials = whatid.dao.TwitterCredentials.query
        
        #api = twitter.Api(consumer_key='consumer_key', consumer_secret='consumer_secret', access_token_key='access_token', access_token_secret='access_token_secret')
        

#https://api.twitter.com/1/statuses/mentions.json?include_entities=true

#https://dev.twitter.com/docs/auth/oauth