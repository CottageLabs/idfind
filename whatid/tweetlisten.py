'''this tracks tweets on twitter and when one comes in with a string to identify,
it tries to identify it and passes back the result as a tweet'''

import twitter

class TweetListen(object):
    def __init__(self):
        pass
        #api = twitter.Api(consumer_key='consumer_key', consumer_secret='consumer_secret', access_token_key='access_token', access_token_secret='access_token_secret')
        

#https://api.twitter.com/1/statuses/mentions.json?include_entities=true

#https://dev.twitter.com/docs/auth/oauth