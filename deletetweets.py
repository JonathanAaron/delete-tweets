import io
import os
import sys
import time
import json

import twitter
from dateutil.parser import parse


class TweetDestroyer(object):
    def __init__(self, twitter_api):
        self.twitter_api = twitter_api

    def destroy(self, tweet_id):
        try:
            print("delete tweet %s" % tweet_id)
            self.twitter_api.DestroyStatus(tweet_id)
            # NOTE: A poor man's solution to honor Twitter's rate limits.
            time.sleep(0.5)
        except twitter.TwitterError as err:
            print("Exception: %s\n" % err.message)


class TweetReader(object):
    def __init__(self, reader, date=None, restrict=None, spare=[], min_likes=0, min_retweets=0):
        self.reader = reader
        if date is not None:
            self.date = parse(date, ignoretz=True).date()
        self.restrict = restrict
        self.spare = spare
        self.min_likes = 0 if min_likes is None else min_likes
        self.min_retweets = 0 if min_retweets is None else min_retweets

    def read(self):
        for row in self.reader:
            if row.get("created_at", "") != "":
                tweet_date = parse(row["created_at"], ignoretz=True).date()
                if self.date != "" and \
                        self.date is not None and \
                        tweet_date >= self.date:
                    continue

            if (self.restrict == "retweet" and
                    not row.get("full_text").startswith("RT @")) or \
                    (self.restrict == "reply" and
                     row.get("in_reply_to_user_id_str") == ""):
                continue

            if row.get("id_str") in self.spare:
                continue

            if (self.min_likes > 0 and int(row.get("favorite_count")) >= self.min_likes) or \
                    (self.min_retweets > 0 and int(row.get("retweet_count")) >= self.min_retweets):
                continue

            yield row


def delete(tweetjs_path, date, r, s, min_l, min_r):
    with io.open(tweetjs_path, mode="r", encoding="utf-8") as tweetjs_file:
        count = 0

        api = twitter.Api(consumer_key=os.environ["TWITTER_CONSUMER_KEY"],
                          consumer_secret=os.environ["TWITTER_CONSUMER_SECRET"],
                          access_token_key=os.environ["TWITTER_ACCESS_TOKEN"],
                          access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"])
        destroyer = TweetDestroyer(api)

        tweets = json.loads(tweetjs_file.read()[25:])
        for row in TweetReader(tweets, date, r, s, min_l, min_r).read():
            destroyer.destroy(row["id_str"])
            count += 1

        print("Number of deleted tweets: %s\n" % count)

    sys.exit()
