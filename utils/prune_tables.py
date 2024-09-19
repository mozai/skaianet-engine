#!/usr/bin/python3
" maintenance on the tables that constantly increase "
# not doing explicit SQL here because hey maybe in the future it'll be
#  MongoDB or XML or textfile who knows

import sys
sys.path.append('/srv/radio/engine')
import skaianet


# delete rows from tables older than this in days
#   default in skaianet.py was 365 days
MAXAGE = 366


def main():
    " Deploy cruxtruder "
    # it's this simple
    if sys.stdout.isatty():
        print(f" trimming rows from recent table older than {MAXAGE} days")
    skaianet.trimrecent(MAXAGE)
    if sys.stdout.isatty():
        print(f" trimming rows from requests table older than {MAXAGE} days")
    skaianet.trimrequests(MAXAGE)


main()
