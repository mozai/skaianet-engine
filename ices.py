###
# Copyright (c) 2015, George Burfeind (Kitty)
# All rights reserved.
#
# This file is part of skaianet-engine.
#
# skaianet-engine is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# skaianet-engine is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with skaianet-engine.  If not, see <http://www.gnu.org/licenses/>.
###
# -- ices (v0.2) USES PYTHON2.7 NOT PYTHON3 -- #
import skaianet
import json
import os
import time
from urllib2 import Request, urlopen

#  ices (v0.2) expects either ices.py or ices.pm to have the following functions:
#  ices_get_next() : return full path to an audio file.
#    above is MANDITORY, all others are optional
#  ices_init() , ices_shutdown() : called on startup and just before shutdown
#  ices_get_metadata() : if returns string, use it instead of inspecting ogg/mp3 file
#  ices_get_lineno() : inserted into the cue file as the current line number in the playlist (???)

JINGLES_PLAY = False
# minimum # of seconds between jingles (30-ish minutes)
JINGLE_INTERVAL = 30 * 60
# timestamp of last time a jingle was played
JINGLE_LASTTIME = 0

# info about current mp3 file (only way to pass it to ices_get_metadata()
CURRENTMP3 = {}


def ices_init():
    " called right after ices starts up "
    skaianet._dprint('ices_init()')
    skaianet.initdb()
    return 1


def ices_shutdown():
    " called just before ices shuts down "
    skaianet._dprint('ices_shutdown()')
    skaianet.closedb()
    return 1


def _ices_get_stats(stream=None):
    " ask icecast daemon for status. can specify a stream by mountpoint "
    if stream:
        req = Request('http://localhost:8000/status-json.xsl?mount={}'.format(stream))
    else:
        req = Request('http://localhost:8000/status-json.xsl')
    try:
        res = urlopen(req, timeout=1)
        answer = json.loads(res.read().decode('utf8'))
        answer = answer['icestats']
    except Exception as err:
        # TODO: what should I do if it fails?
        answer = {'error': err}
        answer = {}
    return answer


def ices_get_next():
    """ pick next audio file from jingles, requests or random
    and update the recent table. return full path to audio file
    """
    global JINGLE_LASTTIME
    global CURRENTMP3
    now = time.gmtime()
    if JINGLES_PLAY and ((now - JINGLE_LASTTIME) > JINGLE_INTERVAL):
        CURRENTMP3 = skaianet.getjingle()
        JINGLE_LASTTIME = now
        fullpath = os.path.join(skaianet.config.jinglepath, CURRENTMP3['filepath'])
    elif skaianet.requestqueued():
        CURRENTMP3 = skaianet.getrequest()
        fullpath = os.path.join(skaianet.config.librarypath, CURRENTMP3['filepath'])
    else:
        CURRENTMP3 = skaianet.getrandomsong()
        fullpath = os.path.join(skaianet.config.librarypath, CURRENTMP3['filepath'])
    icestats = _ices_get_stats()
    listencount = None
    if 'source' in icestats:
        if isinstance(icestats['source'], dict):
            listencount = icestats['source']['listeners']
        elif isinstance(icestats['source'], list):
            listencount = icestats['source'][0]['listeners']
    skaianet.setplaying(
        CURRENTMP3["id"],
        CURRENTMP3["title"],
        CURRENTMP3["artist"],
        CURRENTMP3["album"],
        CURRENTMP3["length"],
        CURRENTMP3["reqname"],
        CURRENTMP3["reqsrc"],
        listencount)
    skaianet._dprint('ices_get_next() = {}'.format(fullpath))
    return '{}'.format(fullpath)  # if I use just "return fullpath" ices says "playlist empty" ???


def ices_get_metadata():
    " returns a string to use instead of inspecting metadata of mp3 file "
    mdstring = '{artist} - {title}'.format(**CURRENTMP3)
    skaianet._dprint('ices_get_metadata() = {}'.format(mdstring))
    return mdstring

if __name__ == '__main__':
    # test mode
    skaianet.setplaying = lambda *args, **kwargs: False
    skaianet.config.debug = True
    ices_init()
    fullpath = ices_get_next()
    mdstring = ices_get_metadata()
    ices_shutdown()
