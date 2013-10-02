#!/usr/bin/env python
"""
Deletes tweets that are older than max_tweet_age age from your timeline.
"""

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

# For matching and converting twitter timestamp to Unix time.
# Twitter timestamp: Thu Jul 25 19:10:38 +0000 2013
TWITTER_TIMESTAMP_PATTERN = '%a %b %d %H:%M:%S +0000 %Y'

# Used while working out the maximum tweet age.
ONE_DAY = 86400


def main():
    """Main"""
    logging.info("Starting TweetDelete")
    api = twitter.Api(
        consumer_key=CONFIG.get('api', 'consumer_key'),
        consumer_secret=CONFIG.get('api', 'consumer_secret'),
        access_token_key=CONFIG.get('api', 'access_token_key'),
        access_token_secret=CONFIG.get('api', 'access_token_secret')
    )

    max_age_difference = CONFIG.getint('general', 'max_tweet_age') * ONE_DAY
    now = int(time.strftime('%s'))

    delete_count = 0
    max_tweet_id = None

    while True:
        logging.debug("Fetching timeline with count={count} and "
                      "max_id={max_id}".format(count=MAX_TIMELINE_COUNT,
                                               max_id=max_tweet_id))

        statuses = api.GetUserTimeline(count=MAX_TIMELINE_COUNT,
                                       max_id=max_tweet_id)
        status_count = len(statuses)

        if not status_count:
            break

        logging.info("Processing {count} statuses.".format(count=status_count))

        for status in statuses:
            created_at = status.GetCreatedAt()
            tweet_id = status.GetId()
            tweet = status.GetText()

            # Twitter timestamp: Thu Jul 25 19:10:38 +0000 2013
            tweet_unix_timestamp = int(time.strftime('%s', time.strptime(
                created_at, TWITTER_TIMESTAMP_PATTERN)))

            if now - tweet_unix_timestamp > max_age_difference:
                logging.info("Deleting status #{id}: {date} -> {tweet}".format(
                    id=tweet_id,
                    date=created_at,
                    tweet=tweet))
                try:
                    api.DestroyStatus(tweet_id, trim_user=True)
                    delete_count += 1
                except twitter.TwitterError as exc:
                    logging.debug(exc)
                    return 1

            # Always set this one lower than the tweet_id, so that when we
            # request the next page we don't end up with one that we already
            # processed.
            max_tweet_id = tweet_id - 1

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
