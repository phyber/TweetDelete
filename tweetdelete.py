#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
import ConfigParser as configparser
import logging
import os
import StringIO
import sys
import time
import twitter

DEFAULT_CONFIG = """
[general]
max_tweet_age: 180
log_file: ~/.local/var/log/tweetdelete.log
log_format: %(asctime)s: %(name)s %(levelname)s %(message)s
"""
USER_CONFIG_PATH = '~/.tweetdelete.conf'

# Maximum number of tweets we can request. Set my twitter.
# https://dev.twitter.com/docs/api/1.1/get/statuses/user_timeline
MAX_TIMELINE_COUNT = 200


def main():
    """Main"""
    logging.info("Starting TweetDelete")
    api = twitter.Api(
        consumer_key=CONFIG.get('api', 'consumer_key'),
        consumer_secret=CONFIG.get('api', 'consumer_secret'),
        access_token_key=CONFIG.get('api', 'access_token_key'),
        access_token_secret=CONFIG.get('api', 'access_token_secret')
    )

    max_age_difference = CONFIG.getint('general', 'max_tweet_age') * 86400
    now = int(time.strftime('%s'))
    delete_count = 0
    statuses = api.GetUserTimeline(count=MAX_TIMELINE_COUNT)

    for status in statuses:
        created_at = status.GetCreatedAt()

        # Twitter timestamp: Thu Jul 25 19:10:38 +0000 2013
        tweet_timestamp = int(time.strftime('%s', time.strptime(
            created_at, '%a %b %d %H:%M:%S +0000 %Y')))

        if now - tweet_timestamp > max_age_difference:
            tweet_id = status.GetId()
            tweet = status.GetText()
            logging.info("Deleting: {date} -> {tweet}".format(
                date=created_at,
                tweet=tweet))
            try:
                api.DestroyStatus(tweet_id, trim_user=True)
                delete_count = delete_count + 1
            except twitter.TwitterError as exc:
                logging.debug(exc)
                return 1

    logging.info("Finished TweetDelete. {count} tweets deleted.".format(
        count=delete_count))


if __name__ == '__main__':
    CONFIG = configparser.ConfigParser()
    CONFIG.readfp(StringIO.StringIO(DEFAULT_CONFIG))
    CONFIG.read(os.path.expanduser(USER_CONFIG_PATH))
    LOG_FILE = CONFIG.get('general', 'log_file')
    try:
        LOG_PATH = os.path.dirname(os.path.expanduser(LOG_FILE))
        if not os.path.exists(LOG_PATH):
            os.makedirs(LOG_PATH)
    except os.error as exc:
        logging.debug(exc)
        sys.exit(1)

    logging.basicConfig(
        level=logging.INFO,
        filename=os.path.expanduser(LOG_FILE),
        format=CONFIG.get('general', 'log_format', True),
    )
    sys.exit(main())
