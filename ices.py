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

from string import *
import sys
import datetime
import config
import skaianet
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

intervalcount = 0


def ices_init():
    skaianet.initdb()
    skaianet.checkdb()
    return 1


def ices_shutdown():
    skaianet.closedb()
    return 1


def ices_get_next():
    global intervalcount
    global currentMp3
    intervalcount += 1
    print intervalcount
    if intervalcount >= 5:
        intervalcount = 0
        currentMp3 = {
            "title": ["Skaianet Ad Hatorade"],
            "artist": ["Advertisement"]}
        return '/home/kitty/ices/jingles/Skaianet Ad Hatorade.mp3'
    skaianet._dprint('Next Song')
    reqCountC = skaianet.db.cursor()
    reqCountC.execute('SELECT * FROM requests LIMIT 1')
    reqPotato = reqCountC.fetchall()
    reqCount = reqCountC.rowcount
    reqCountC.close()
    nextmp3 = skaianet.db.cursor()
    reqname = ""
    reqsrc = ""
    if reqCount > 0:
        print 'REQUEST THERE, NEED TO PROCESS'
        nextmp3q = ("SELECT id,filepath FROM library WHERE id=%(song)s")
        nextmp3.execute(nextmp3q, {'song': reqPotato[0][1]})
        reqname = reqPotato[0][2]
        reqsrc = reqPotato[0][3]
    else:
        print 'NO REQUEST, MOVING ON'
        nextmp3q = (
            "SELECT id,filepath FROM library WHERE autoplay=1"
            " ORDER BY RAND() LIMIT 1")
        nextmp3.execute(nextmp3q)
    nextmp3p = nextmp3.fetchall()[0]
    nextmp3.close()
    if reqCount > 0:
        reqRemove = skaianet.db.cursor()
        reqRemove.execute(
            "DELETE FROM requests WHERE id=%(reqid)s",
            {'reqid': reqPotato[0][0]})
        reqRemove.close()
        skaianet.db.commit()
    currentMp3 = MP3(nextmp3p[1], ID3=EasyID3)
    skaianet.setplaying(
        nextmp3p[0],
        currentMp3["title"][0].encode('utf-8'),
        currentMp3["artist"][0].encode('utf-8'),
        currentMp3["album"][0].encode('utf-8'),
        round(currentMp3.info.length))
    return '{}'.format(nextmp3p[1])


def ices_get_metadata():
    mdstring = currentMp3["artist"][0].encode('utf-8') + ' - ' + \
        currentMp3["title"][0].encode('utf-8')
    skaianet._dprint('Title: ' + mdstring)
    return mdstring
