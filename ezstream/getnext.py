#!/usr/bin/env python
" for ezstream, fetch next song to play and update state in database "
# TODO: rewrite this in something faster like golang
#       but then I'm not using skaianet.py anymore, hrm.

import os
import sys
import time
import requests
sys.path.append('/srv/radio/engine')
import skaianet

# do we play station identification?
JINGLES_PLAY = False
# if it's been this many seconds, play another stn id
JINGLES_INTERVAL = 60*30


def _ices_get_stats(stream=None):
    " ask icecast daemon for status. can specify a stream by mountpoint "
    try:
        if stream:
            res = requests.get(
                f"http://localhost:8000/status-json.xsl?mount={stream}")
        else:
            res = requests.get("http://localhost:8000/status-json.xsl")
        res.raise_for_status()
        answer = res.json()
        answer = answer['icestats']
    except Exception:
        # TODO: what should I do if it fails?
        answer = {}
    return answer


def get_next():
    " what do I play next? "
    now = time.gmtime()
    nextsong = None
    jinglepath = skaianet.config["library.paths"].get("jingles")
    musicpath = skaianet.config["library.paths"].get("music")
    if JINGLES_PLAY and (JINGLES_INTERVAL > 60):
        jingle_lasttime = now  # QUACK if you don't have a real value jingles never play
        # TODO jingle_lasttime = skaianet.getlastjingletime()
        if (now - jingle_lasttime) > JINGLES_INTERVAL:
            nextsong = skaianet.getjingle()
        if nextsong:
            skaianet.setplaying(nextsong["id"], None, None, 0, jingle=True)
            return os.path.join(jinglepath, nextsong['filepath'])
    if not nextsong:
        nextsong = skaianet.getrequest()
    if not nextsong:
        nextsong = skaianet.getrandomsong()
    if not nextsong:
        raise Exception('Error: both getrequest() and getrandomsong() failed')
    fullpath = os.path.join(musicpath, nextsong['filepath'])
    # measure how many listeners when the song started
    icestats = _ices_get_stats()
    listencount = None
    if 'source' in icestats:
        if isinstance(icestats['source'], dict):
            listencount = icestats['source']['listeners']
        elif isinstance(icestats['source'], list):
            listencount = icestats['source'][0]['listeners']
    # update nowplaying state in db
    skaianet.setplaying(nextsong["id"], nextsong.get("reqid"), listencount)
    return f"{fullpath}"


def main():
    " :33 < *ac drops a new song from her mouths for you* "
    skaianet.initdb()
    nextsong = get_next()
    print(f"{nextsong}")
    skaianet.closedb()


main()
