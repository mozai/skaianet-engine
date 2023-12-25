#!/usr/bin/env python
" for ezstream, fetch next song to play and update state in database "
# TODO: rewrite this in something faster like golang
#       but then I'm not using skaianet.py anymore, hrm.
# there could be a get_metadata.sh but ezstream should sense it for .mp3 files

import os
import sys
import time
import requests
sys.path.append('/srv/radio/engine')
import skaianet

# TODO: need to save "last bumper played" state in database
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
    if JINGLES_PLAY:
        # get jingle_lasttime
        jingle_lasttime = now  # QUACK blocks all jingles
        if (now - jingle_lasttime) > JINGLES_INTERVAL:
            nextsong = skaianet.getjingle()
        if nextsong:
            # set jingle_lasttime
            fullpath = os.path.join(
                skaianet.config.jinglepath, nextsong['filepath'])
            return "{fullpath}"
    if not nextsong:
        nextsong = skaianet.getrequest()
    if not nextsong:
        nextsong = skaianet.getrandomsong()
    if not nextsong:
        raise Exception('Error: both getrequest() and getrandomsong() failed')
    fullpath = os.path.join(skaianet.config.librarypath, nextsong['filepath'])
    # measure how many listeners when the song started
    icestats = _ices_get_stats()
    listencount = None
    if 'source' in icestats:
        if isinstance(icestats['source'], dict):
            listencount = icestats['source']['listeners']
        elif isinstance(icestats['source'], list):
            listencount = icestats['source'][0]['listeners']
    # update nowplaying state in db
    skaianet.setplaying(nextsong["id"], nextsong["title"],
                        nextsong["artist"], nextsong["album"], nextsong["length"],
                        nextsong["reqname"], nextsong["reqsrc"], listencount)
    return f"{fullpath}"


def main():
    " :33 < *ac drops a new song from her mouths for you* "
    # skaianet.setplaying = lambda *args, **kwargs: False  # DEBUG
    skaianet.initdb()
    nextsong = get_next()
    print(f"{nextsong}")
    skaianet.closedb()


main()
