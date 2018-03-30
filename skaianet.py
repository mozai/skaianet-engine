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
# TODO: turn off database commits so we can test the set*() methods
from __future__ import print_function  # because ices still uses python 2.x
from collections import defaultdict
import config
import datetime
import mutagen
import mysql.connector
import random
import re
import os

global db


def _dprint(msg):
    """ Print a debug line.
    This is a simple function.  If I got any more meta, I'd be telling
    you about how this is a docstring.
    """
    if config.debug:
        print(datetime.datetime.now().strftime("[%H:%M:%S] ") + msg)


def initdb(autocommit=True):
    """ Initializes the database used for radio control.
    Must be called on it's own at least once before anything that
    calls the database is used.
    ** SHOULD check for proper schema, but does not.
    """
    global db
    _dprint("initdb(commit={})".format(autocommit))
    db = mysql.connector.connect(user=config.dbuser,
                                 password=config.dbpass,
                                 database=config.dbname,
                                 autocommit=autocommit)
    _dprint('  FIXME: should verify schema to make sure it matches expectations')
    return db


def closedb(commit=True):
    """ Ensures all changes are saved before closing the database.
    Should be called only when all DB actions are done.
    """
    _dprint('closedb(commit={})'.format(commit))
    if commit:
        _dprint('  Saving changes to database')
        db.commit()
    else:
        _dprint('  Rolling back any changes')
        db.rollback()   # .close() without .commit() should already do this
    db.close()


def _checklibraryfiles(commit=False):
    # for each file on disk, do we have a row in library table?
    _dprint('_checklibrary(commit={})'.format(commit))
    suggestions = []
    for root, dirs, files in os.walk(config.librarypath):
        for fname in files:
            if not (fname.endswith(".mp3") or fname.endswith(".ogg")):
                continue
            fullpath = os.path.join(root, fname)
            shortpath = fullpath.replace(config.librarypath, '')
            cur = db.cursor()
            sql = "SELECT id FROM library WHERE filepath = %(fullpath) or filepath = %(shortpath) LIMIT 1"

            cur.execute(sql, {'fullpath': fullpath})
            found = cur.fetchall()
            cur.close()
            if found:
                continue
            suggestions.append('new file: {}'.format(shortpath))
            if commit:
                _dprint('  adding {}'.format(shortpath))
                _addsongtodb(fullpath)
    return suggestions


def _checklibrarytable(commit=False):
    # for each row in library table, do we have a file on disk?
    suggestions = []
    mp3libcursor = db.cursor(dictionary=True)
    mp3libcursor.execute("SELECT id, filepath FROM library WHERE autoplay = 1 or requestable = 1 ORDER BY filepath;")
    for row in mp3libcursor.fetchall():
        fullpath = os.path.join(config.librarypath, row['filepath'])
        if os.path.isfile(fullpath):
            continue
        suggestions.append('missing file: {}'.format(fullpath))
        if commit:
            _dprint('  removing {}'.format(row['filepath']))
            _rmsongfromdb(row['id'])
    mp3libcursor.close()
    return suggestions


def checkdb(commit=False):
    """ Check the database against the song library for consistency,
    and vice-versa.  Returns suggested changes. set commit = True to
    implement suggested changes.
    """
    _dprint('checkdb()')
    answer = []
    suggestions = _checklibraryfiles(commit)
    answer.extend(suggestions)
    suggestions = _checklibrarytable(commit)
    answer.extend(suggestions)
    return sorted(answer)


def _addsongtodb(path):
    """ Add a song to the library.
    Takes the path of an MP3 file, and then adds the path and metadata
    to the library database for use in circulation or requests.
    """
    songmeta = getsongmeta(path)
    # { 'album', 'artist', 'title', 'track', 'length', 'website' }
    # TODO: what if some of the songmeta is missing/empty ?
    if path.startswith(config.librarypath):
        songmeta['filepath'] = path.replace(config.librarypath, '')
    else:
        songmeta['filepath'] = path
    cur = db.cursor()
    cur.execute("SELECT id FROM library WHERE filepath = %(filepath)s LIMIT 1", songmeta)
    found = cur.fetchone()
    cur.close()
    cur = db.cursor()
    if found:
        _dprint('_addsongtodb(\"{}\") Updating: '.format(path))
        songmeta['id'] = found[0]
        sql = "UPDATE library SET album = %(album)s, " \
              "artist = %(artist)s, length = %(length)s, " \
              "title = %(title)s, website = %(website)s " \
              "WHERE id = %(id)s"
    else:
        _dprint('_addsongtodb(\"{}\") Inserting: '.format(path))
        sql = "INSERT INTO library " \
              "(title, artist, album, length, website, filepath) " \
              "VALUES (%(title)s, %(artist)s, %(album)s, %(length)s, %(website)s, %(filepath)s)"
    _dprint('  Title: {title} :: Artist: {artist} :: Album: {album}'.format(**songmeta))
    cur.execute(sql, songmeta)
    cur.close()
    cur = db.cursor()
    cur.execute("SELECT id FROM library WHERE filepath = %(filepath)s LIMIT 1", songmeta)
    row = cur.fetchone()
    cur.close()
    return row[0]  # library.id of the new/updated row


def _rmsongfromdb(id):
    """ Remove a song from the library.
    Takes the ID number assigned to a song's database entry and removes
    it from the database.
    """
    _dprint("_rmsongfromdb(\"{}\")".format(id))
    removecursor = db.cursor()
    # don't delete, because library.id is a foreign key to other tables
    # removecursor.execute("DELETE FROM library WHERE id=%(id)s", {'id': id})
    removecursor.execute("UPDATE library SET autoplay = 0, requestable = 0, "
                         "length = NULL WHERE id=%(id)s",
                         {'id': id})
    removecursor.close()


def setplaying(songid, title, artist, album, length,
               reqname='', reqsrc='', listeners=0):
    """ Adds a song to the recently played database.
    This is assuming that this function is called when the song starts
    playing so that the timing can be accurate for linked functions.
    Takes arguments of the songs DB number, title, album, artist,
    length in seconds, and optionally, the person requesting the song,
    and optiononally, how many people are listening right now.
    """
    # TODO: we could get title, artist, album, length from library table or jingle table
    _dprint('setplaying({}, "{}", "{}", "{}", {}, "{}", "{}", {})'.format(
        songid, title, artist, album, length, reqname, reqsrc, listeners))
    query = "INSERT INTO recent " \
            "(songid, title, artist, album, length, " \
            "reqname, reqsrc, time, listeners) " \
            "VALUES (%(songid)s, %(title)s, %(artist)s," \
            "%(album)s, %(length)s, " \
            "%(reqname)s, %(reqsrc)s, CURRENT_TIMESTAMP(), %(listeners)s)"
    data = {'songid': songid,
            'title': title,
            'artist': artist,
            'album': album,
            'length': length,
            'reqname': reqname,
            'reqsrc': reqsrc,
            'listeners': listeners}
    setcursor = db.cursor()
    setcursor.execute(query, data)
    setcursor.close()


def requestqueued():
    """ Checks if there is a request waiting to be processed.
    Takes no arguments, returns True or False.
    """
    # TODO: do we need this? or can getrequest() just return None ?
    cur = db.cursor()
    cur.execute('SELECT id FROM requests LIMIT 1')
    found = cur.fetchone()
    cur.close()
    return found is not None


def _extract_a_url_from_mutagen_mp3(mutagenf):
    # what a clusterfuck
    # can't just use framename, because it could be 'WCOM:full_url' or
    # 'WXXX:' or 'WXXX:None' or 'COMM::eng' or 'COMM::ENG' or 'COMM::XXX'
    # or ....
    diggy = re.compile(r'((f|ht)tps?://[^\s},"\']+)', re.S | re.I)
    # first try the most likely place
    matchobj = diggy.search(str(mutagenf.tags.get('COMM::XXX')))
    if matchobj:
        return matchobj.group(1)
    # then try everywhere else: WXXX first, and COMM::XXX before COMM::eng
    frames = sorted([i for i in mutagenf.tags.keys() if i.startswith('W') or i.startswith('C')], reverse=True)
    for frame in frames:
        matchobj = diggy.search(str(mutagenf.tags[frame]))
        if matchobj:
            return matchobj.group(1)


def _extract_a_url_from_mutagen_ogg(mutagenf):
    diggy = re.compile(r'((f|ht)tps?://[^\s},"\']+)', re.S | re.I)
    for i in ('contact', 'description', 'comment', 'license'):
        for j in mutagenf.get(i, []):
            matchobj = diggy.search(j)
            if matchobj:
                return matchobj.group(1)


def _extract_a_url_from_mutagen(mutagenf):
    " pull a url out of id3v2 or vorbiscomments, expects mutagen.File "
    # god this is so complicated
    if mutagenf.mime[0] == 'audio/mp3':
        return _extract_a_url_from_mutagen_mp3(mutagenf)
    elif mutagenf.mime[0] == 'audio/vorbis':
        return _extract_a_url_from_mutagen_ogg(mutagenf)


def getsongmeta(path):
    """ given filename, return metadata from that file
    for use in inserting/updating rows in the library table
    """
    # provides 'None' for missing tags, eqiv. of NULL in database
    answer = defaultdict(lambda: None)
    if path.endswith('mp3'):
        f = mutagen.File(path)
        # list of keys at http://id3.org/id3v2.3.0
        answer['album'] = str(f.get('TALB', ''))
        answer['artist'] = str(f.get('TPE1', ''))
        answer['title'] = str(f.get('TIT2', ''))
        answer['length'] = round(f.info.length)
        answer['track'] = int(str(f.get('TRCK', '0')))
        answer['website'] = _extract_a_url_from_mutagen(f)
    elif path.endswith('.ogg'):
        f = mutagen.File(path)
        answer['album'] = str(f.get('ALBUM', ''))
        answer['artist'] = str(f.get('ARTIST', ''))
        answer['title'] = str(f.get('TITLE', ''))
        answer['length'] = round(f.info.length)
        answer['track'] = int(str(f.get('TRACKNUMBER', '0')))
        answer['website'] = _extract_a_url_from_mutagen(f)
    else:
        # TODO: how to analyze other audio/* file types
        raise Exception('unrecognized file type: {}'.format(path))
    for i in answer:
        if answer[i] == '':
            del(answer[i])
    answer['filepath'] = path
    _dprint('getsongmeta("{}") = {}'.format(path, repr(answer)))
    return answer


def getrandomsong():
    """ fetch a song from the library that wasn't recently played
    """
    # actually returns the last-recently-played song of recentlimit + 1
    # could we use 'random_fresh_song' view in db?
    #   that view is based on time not # of songs
    #   and that view fails if entire library is <1 hour in length
    cur = db.cursor(buffered=True, dictionary=True)
    recentlimit = config.recentlimit or 20
    cur.execute("SELECT l.id, l.filepath, l.title, l.artist, l.album, l.length, l.website "
                "FROM (SELECT * FROM library WHERE autoplay = 1 "
                "ORDER BY rand() LIMIT %(range)s) l "
                "LEFT JOIN recent r ON l.id = r.songid "
                "ORDER BY r.time ASC LIMIT 1",
                {'range': recentlimit + 1})
    result = cur.fetchone()
    cur.close()
    assert result  # should never be None
    answer = result.copy()
    answer['reqname'] = ''
    answer['reqsrc'] = ''
    _dprint('getrandomsong() = {}'.format(repr(answer)))
    return answer


def getrequest():
    " returns song data for a valid request if any "
    answer = None
    while answer is None:
        reqcursor = db.cursor(dictionary=True)
        reqcursor.execute(
            "SELECT id,reqid,reqname,reqsrc FROM requests LIMIT 1")
        reqdata = reqcursor.fetchone()
        reqcursor.close()
        if reqdata is None:
            break
        reqrmcursor = db.cursor()
        reqrmcursor.execute("DELETE FROM requests WHERE id=%(id)s",
                            {'id': reqdata['id']})
        reqrmcursor.close()
        libcursor = db.cursor(dictionary=True)
        libcursor.execute(
            "SELECT id, filepath, title, artist, album, length, "
            "website FROM library WHERE id=%(song)s LIMIT 1",
            {'song': reqdata['reqid']})
        libdata = libcursor.fetchone()
        libcursor.close()
        if libcursor:
            answer = libdata.copy()
            answer['reqname'] = reqdata['reqname']
            answer['reqsrc'] = reqdata['recsrc']
    _dprint('getrequest() = {}'.format(repr(answer)))
    return answer


def getjingle():
    # TODO: jingles should also be in the database, as a separate table like 'library'
    jinglelist = []
    for root, dirs, files in os.walk(config.jinglepath):
        for file in files:
            if file.endswith(".mp3"):
                jinglelist.append(file)
    jinglepath = config.jinglepath + random.choice(jinglelist)
    jinglemeta = getsongmeta(jinglepath)
    answer = {'id': 0, 'filepath': jinglepath, 'title': 'Advertisement',
              'artist': 'Advertisement', 'album': 'Advertisement',
              'length': jinglemeta['length'], 'website': '',
              'reqname': '', 'reqsrc': ''}
    _dprint('getjingle() = {}'.format(repr(answer)))
    return answer


def getsetting(name, id=1):
    " update the entries in table settings "
    if name not in ('commercialrate', 'repeatcheckrate', 'notifytext'):
        raise ValueError('unexpected setting name "{}"'.format(name))
    cur = db.cursor(buffered=True)
    sql = "SELECT {} FROM settings WHERE id=%(id)s".format(name)
    data = {'id': id}
    cur.execute(sql, data)
    row = cur.fetchone()
    cur.close()
    answer = row[0]
    _dprint('getsetting("{}", {}) = {}'.format(name, id, repr(answer)))
    return answer


def setsetting(name, value, id=1):
    " update the entries in table settings "
    _dprint('setsetting("{}", "{}", {})'.format(name, value, id))
    if name not in ('commercialrate', 'repeatcheckrate', 'notifytext'):
        raise ValueError('unexpected setting name "{}"'.format(name))
    reqcursor = db.cursor()
    reqcursor.execute("UPDATE settings SET {} = %(v)s where id=%(id)s".format(name), {'v': value, 'id': id})
    reqcursor.close()


if __name__ == '__main__':
    print("*** testing skaianet module")
    # TODO: make sure we turn off database commits so we can test the set*() methods
    config.debug = True
    initdb(autocommit=False)
    suggestions = checkdb(commit=False)
    # _dprint("checkdb() suggestion count: {}".format(len(suggestions)))
    # id = _addsongtodb(example.mp3)
    # _rmsongfromdb(id)
    # setplaying(id,  bluh bluh)
    song = getrandomsong()
    getsongmeta(os.join(config.librarypath, song['filepath']))
    _extract_a_url_from_mutagen(mutagen.File(os.join(config.librarypath, song['filepath'])))
    requestqueued()
    getrequest()
    getjingle()
    getsetting('name')
    # setsetting('name', 'Skaianet Radio')
    closedb(commit=False)
