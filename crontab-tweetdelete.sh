#!/bin/sh
# Small script to quickly crontab tweetdelete.py if it's in a VirtualEnv.
# This script will cd into and activate the VirtualEnv before executing
# tweetdelete.py
VIRTUALENV_DIR="${0%/*}"
cd "${VIRTUALENV_DIR}"
. activate
tweetdelete.py
