#!/usr/bin/env python3
" heart of skaianet python code "
###
# original version bears a copyright by George "Kitty" Burfeind
# and a statement that it is shared for public use as per
# the GNU General Public License v3 <http://www.gnu.org/licenses/>
# ... which means all derivative works must bear the same license for use.
###

# TODO: turn off database commits so we can test the set*() methods
from collections import defaultdict
import configparser
import datetime
import os
import random
import re
import time
import mutagen
import mysql.connector

# global var for the database connection
DBCONN = None

# global to hold config settings
CONFIG = configparser.ConfigParser()
CONFIG.read("/home/radio/engine/config.ini")


def _dprint(msg):
    """ Print a debug line.
    This is a simple function.  If I got any more meta, I'd be telling
    you about how this is a docstring.
    """
    if CONFIG["engine"].get("debug"):
        print(datetime.datetime.now().strftime("[%H:%M:%S] ") + msg)


def initdb(autocommit=True):
    """ Initializes the database used for radio control.
    Must be called on it's own at least once before anything that
    calls the database is used.
    ** SHOULD check for proper schema, but does not.
    """
    global DBCONN
    _dprint(f"initdb(commit={autocommit})")
    DBCONN = mysql.connector.connect(user=CONFIG["db.mysql"]["dbuser"],
                                     password=CONFIG["db.mysql"]["dbpass"],
                                     database=CONFIG["db.mysql"]["dbname"],
                                     autocommit=autocommit)
    # FIXME: should verify schema to make sure it matches expectations
    return DBCONN


def closedb(commit=True):
    """ Ensures all changes are saved before closing the database.
    Should be called only when all DB actions are done.
    """
    _dprint(f"closedb(commit={commit})")
    if commit:
        _dprint("  Saving changes to database")
        DBCONN.commit()
    else:
        _dprint("  Rolling back any changes")
        DBCONN.rollback()   # .close() without .commit() should already do this
    DBCONN.close()


def _checklibraryfiles(commit=False):
    # for each file on disk, do we have a row in library table?
    _dprint(f"_checklibrary(commit={commit})")
    suggestions = []
    librarypath = CONFIG["library.paths"].get("music")
    for root, _, files in os.walk(librarypath):
        for fname in files:
            if not (fname.endswith(".mp3") or fname.endswith(".ogg")):
                continue
            fullpath = os.path.join(root, fname)
            shortpath = fullpath.replace(librarypath, '')
            cur = DBCONN.cursor()
            sql = "SELECT id FROM library WHERE filepath = %(fullpath)s or filepath = %(shortpath)s LIMIT 1"
            cur.execute(sql, {'fullpath': fullpath, 'shortpath': shortpath})
            found = cur.fetchall()
            cur.close()
            if found:
                continue
            suggestions.append(f"new file: {shortpath}")
            if commit:
                _dprint(f"  adding {shortpath}")
                _addsongtodb(fullpath)
    return suggestions


def _checklibrarytable(commit=False):
    # for each row in library table, do we have a file on disk?
    suggestions = []
    mp3libcursor = DBCONN.cursor(dictionary=True)
    mp3libcursor.execute(
        "SELECT id, filepath FROM library WHERE autoplay = 1 or requestable = 1 ORDER BY filepath;")
    librarypath = CONFIG["library.paths"].get("music")
    for row in mp3libcursor.fetchall():
        fullpath = os.path.join(librarypath, row['filepath'])
        if os.path.isfile(fullpath):
            continue
        suggestions.append(f"missing file: {fullpath}")
        if commit:
            _dprint(f"  removing {fullpath}")
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
    librarypath = CONFIG["library.paths"].get("music")
    if path.startswith(librarypath):
        songmeta['filepath'] = path.replace(librarypath, '')
    else:
        songmeta['filepath'] = path
    cur = DBCONN.cursor()
    cur.execute(
        "SELECT id FROM library WHERE filepath = %(filepath)s LIMIT 1", songmeta)
    found = cur.fetchone()
    cur.close()
    cur = DBCONN.cursor()
    if found:
        _dprint(f"_addsongtodb(\"{path}\") Updating: ")
        songmeta['id'] = found[0]
        sql = "UPDATE library SET album = %(album)s, " \
              "artist = %(artist)s, length = %(length)s, " \
              "title = %(title)s, website = %(website)s " \
              "WHERE id = %(id)s"
    else:
        _dprint("_addsongtodb(\"{path}\") Inserting: ")
        sql = "INSERT INTO library " \
              "(title, artist, album, length, website, filepath) " \
              "VALUES (%(title)s, %(artist)s, %(album)s, %(length)s, %(website)s, %(filepath)s)"
    _dprint(f"""  Title: {songmeta["title"]} :: Artist: {songmeta["artist"]} :: Album: {songmeta["album"]}""")
    cur.execute(sql, songmeta)
    cur.close()
    cur = DBCONN.cursor()
    cur.execute(
        "SELECT id FROM library WHERE filepath = %(filepath)s LIMIT 1", songmeta)
    row = cur.fetchone()
    cur.close()
    return row[0]  # library.id of the new/updated row


def _rmsongfromdb(idnum):
    """ Remove a song from the library.
    Takes the ID number assigned to a song's database entry and removes
    it from the database.
    """
    _dprint(f"_rmsongfromdb(\"{idnum}\")")
    removecursor = DBCONN.cursor()
    # don't delete, because library.id is a foreign key to other tables
    # removecursor.execute("DELETE FROM library WHERE id=%(id)s", {'id': idnum})
    removecursor.execute(
        "UPDATE library SET autoplay = 0, requestable = 0, length = NULL WHERE id=%(id)s", {'id': idnum})
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
    _dprint(f"""setplaying({songid}, "{title}", "{artist}", "{album}", {length}, "{reqname}", "{reqsrc}", {listeners})""")
    setcursor = DBCONN.cursor()
    query = "INSERT INTO recent (songid, title, artist, album, length, reqname, reqsrc, time, listeners) " \
        "VALUES (%(songid)s, %(title)s, %(artist)s, %(album)s, %(length)s, %(reqname)s, %(reqsrc)s, CURRENT_TIMESTAMP(), %(listeners)s)"
    data = {'songid': songid, 'title': title, 'artist': artist, 'album': album,
            'length': length, 'reqname': reqname, 'reqsrc': reqsrc, 'listeners': listeners}
    setcursor.execute(query, data)
    query = "UPDATE library SET last_played = CURRENT_TIMESTAMP() WHERE id = %(songid)s"
    data = {'songid': songid}
    setcursor.execute(query, data)
    setcursor.close()


def getplaying():
    """ returns object that describes curently-playing song """
    _dprint(u'getplaying()')
    cur = DBCONN.cursor(dictionary=True)
    cur.execute("SELECT * FROM recent ORDER BY time DESC LIMIT 1")
    result = cur.fetchone()
    cur.close()
    assert result  # should never be None
    answer = result.copy()
    return answer


def requestqueued():
    """ Checks if there is a request waiting to be processed.
    Takes no arguments, returns True or False.
    """
    # TODO: do we need this? or can getrequest() just return None ?
    cur = DBCONN.cursor()
    cur.execute('SELECT id FROM requests LIMIT 1')
    found = cur.fetchone()
    cur.close()
    return found is not None


def _extract_a_url_from_mutagen_mp3(mutagenf):
    # what a clusterfuck
    # can't just use framename, because it could be 'WCOM:full_url' or
    # 'WXXX:' or 'WXXX:None' or 'COMM::eng' or 'COMM::ENG' or 'COMM::XXX'
    # or ....
    # and!  it will read id3 tags before id3v2 tags which means truncated comments
    diggy = re.compile(r'''((f|ht)tps?://[^ }"',]+)''', re.S | re.I)
    # first try the most likely place
    matchobj = diggy.search(str(mutagenf.tags.get('COMM::XXX')))
    if matchobj:
        return matchobj.group(1)
    # then try everywhere else: WXXX first, and COMM::XXX before COMM::eng
    frames = sorted([i for i in mutagenf.tags.keys() if i.startswith(
        'W') or i.startswith('C')], reverse=True)
    for frame in frames:
        matchobj = diggy.search(str(mutagenf.tags[frame]))
        if matchobj:
            return matchobj.group(1)
    return None


def _extract_a_url_from_mutagen_ogg(mutagenf):
    diggy = re.compile(r'((f|ht)tps?://[^\s},"\']+)', re.S | re.I)
    for i in ('contact', 'description', 'comment', 'license'):
        for j in mutagenf.get(i, []):
            matchobj = diggy.search(j)
            if matchobj:
                return matchobj.group(1)
    return None


def _extract_a_url_from_mutagen(mutagenf):
    " pull a url out of id3v2 or vorbiscomments, expects mutagen.File "
    # god this is so complicated
    if mutagenf.mime[0] == 'audio/vorbis':
        return _extract_a_url_from_mutagen_ogg(mutagenf)
    if mutagenf.mime[0] == 'audio/mp3':
        return _extract_a_url_from_mutagen_mp3(mutagenf)
    return None


def getsongmeta(path):
    """ given filename, return metadata from that file
    for use in inserting/updating rows in the library table
    """
    # provides 'None' for missing tags, eqiv. of NULL in database
    answer = defaultdict(lambda: None)
    if path.endswith('mp3'):
        i = mutagen.File(path)
        # list of keys at http://id3.org/id3v2.3.0
        answer['album'] = str(i.get('TALB', ''))
        answer['artist'] = str(i.get('TPE1', ''))
        answer['title'] = str(i.get('TIT2', ''))
        answer['length'] = round(i.info.length)
        answer['track'] = int(str(i.get('TRCK', '0')))
        answer['website'] = _extract_a_url_from_mutagen(i)
    elif path.endswith('.ogg'):
        i = mutagen.File(path)
        answer['album'] = str(i.get('ALBUM', ''))
        answer['artist'] = str(i.get('ARTIST', ''))
        answer['title'] = str(i.get('TITLE', ''))
        answer['length'] = round(i.info.length)
        answer['track'] = int(str(i.get('TRACKNUMBER', '0')))
        answer['website'] = _extract_a_url_from_mutagen(i)
    else:
        # TODO: how to analyze other audio/* file types
        raise Exception(f"unrecognized file type: {path}")
    for i in list(answer.keys()):
        if answer[i] == '':
            del(answer[i])
    answer['filename'] = os.path.basename(path)
    answer['filepath'] = path
    _dprint(f"""getsongmeta("{path}") = {answer}""")
    return answer


def getrandomsong():
    """ fetch a song from the library that wasn't recently played
    """
    # TODO: should use a stored procedure or view in sql since this darn thing
    #   needs to be restarted every time I want to make a change >_<

    # actually returns the last-recently-played song of recentlimit + 1
    cur = DBCONN.cursor(buffered=True, dictionary=True)
    #recentlimit = CONFIG["engine"].get("recentlimit") or 20
    now = time.gmtime()
    if (now.tm_mon == 12 and now.tm_mday > 14 and random.random() < 0.334):
        # it's around christmas, play the christmas songs more often
        # TODO: have a 'christmas' tag on songs, or have a christmas sublist, only 17 songs currently
        # create or replace view random_christmas_song AS select * from library where autoplay = 1 AND (album = "Homestuck for the Holidays" OR title like "%hristmas%") order by rand() limit 1;
        cur.execute("SELECT * FROM random_christmas_song")
    else:
        # cur.execute("SELECT l.* FROM (SELECT * FROM library WHERE autoplay = 1 ORDER BY rand() LIMIT %(range)s) l "
        #            "LEFT JOIN recent ON l.id = recent.songid ORDER BY recent.time ASC LIMIT 1",
        #            {'range': recentlimit + 1})
        # create or replace view `random_fresh_song` AS select * from library where autoplay = 1 and not id in (select songid from recent where time > current_timestamp() - interval 1 hour) order by rand() limit 1;
        # create or replace view `random_fresh_song` AS SELECT * FROM (SELECT * FROM library WHERE autoplay = 1 ORDER BY rand() LIMIT 20) AS subquery ORDER BY last_played ASC LIMIT 1;
        cur.execute("SELECT * FROM random_fresh_song")
    result = cur.fetchone()
    cur.close()
    assert result  # should never be None
    answer = result.copy()
    answer['reqname'] = ''
    answer['reqsrc'] = ''
    _dprint(f"getrandomsong() = {answer}")
    return answer


def getrequest():
    " returns song data for a valid request if any "
    answer = None
    while answer is None:
        reqcursor = DBCONN.cursor(dictionary=True)
        reqcursor.execute(
            "SELECT id, reqid, reqname, reqsrc FROM requests LIMIT 1")
        reqdata = reqcursor.fetchone()
        reqcursor.close()
        if reqdata is None:
            break
        reqrmcursor = DBCONN.cursor()
        reqrmcursor.execute("DELETE FROM requests WHERE id=%(id)s",
                            {'id': reqdata['id']})
        reqrmcursor.close()
        libcursor = DBCONN.cursor(dictionary=True)
        libcursor.execute(
            "SELECT id, filepath, title, artist, album, length, "
            "website FROM library WHERE id=%(song)s and requestable = 1 LIMIT 1",
            {'song': reqdata['reqid']})
        libdata = libcursor.fetchone()
        libcursor.close()
        if libcursor:
            answer = libdata.copy()
            answer['reqname'] = reqdata['reqname']
            answer['reqsrc'] = reqdata['reqsrc']
    _dprint("getrequest() = {answer}")
    return answer


def getjingle():
    " summon a random jingle soundfile from the library "
    # TODO: jingles should also be in the database, as a separate table like 'library'
    jinglelist = []
    jinglepath = CONFIG["library.paths"].get("jingles")
    for _, _, files in os.walk(jinglepath):
        for file in files:
            if file.endswith(".mp3"):
                jinglelist.append(file)
    jinglepath = os.path.join(jinglepath, random.choice(jinglelist))
    jinglemeta = getsongmeta(jinglepath)
    answer = {'id': 0, 'filepath': jinglepath, 'title': 'Advertisement',
              'artist': 'Advertisement', 'album': 'Advertisement',
              'length': jinglemeta['length'], 'website': '',
              'reqname': '', 'reqsrc': ''}
    _dprint(f"getjingle() = {answer}")
    return answer


def getsetting(name):
    " update the entries in table settings "
    cur = DBCONN.cursor(buffered=True)
    sql = f"SELECT value FROM settings WHERE name=%(name)s"
    data = {'name': name}
    cur.execute(sql, data)
    row = cur.fetchone()
    cur.close()
    answer = row[0]
    _dprint(f"""getsetting("{name}") = {answer}""")
    return answer


def setsetting(name, value):
    " update the entries in table settings "
    _dprint(f"""setsetting("{name}", "{value}")""")
    reqcursor = DBCONN.cursor()
    reqcursor.execute(f"INSERT INTO settings (name, value) VALUES (%(n)s, %(v)s) ON DUPLICATE KEY UPDATE value = %(v)s", {'n': name, 'v': value})
    reqcursor.close()


def _test():
    " if launched from command line, run tests "
    print("*** testing skaianet module")
    # TODO: make sure we turn off database commits so we can test the set*() methods
    CONFIG["engine"]["debug"] = "true"
    initdb(autocommit=False)
    suggestions = checkdb(commit=False)
    print(f"checkdb() suggestion count: {len(suggestions)}")
    # next three write to the db, bad idea during a test
    # idnum = _addsongtodb(example.mp3)
    # _rmsongfromdb(idnum)
    # setplaying(idnum,  bluh bluh)
    song = getrandomsong()
    print(f"getrandomsong(): {song}")
    songfile = os.path.join(CONFIG["library.paths"]["music"], song['filepath'])
    stuff = getsongmeta(songfile)
    print(f"getsongmeta({songfile}): {stuff}")
    stuff = _extract_a_url_from_mutagen(mutagen.File(songfile))
    print(f"_extract_a_url_from_mutagen({songfile}): {stuff}")
    stuff = requestqueued()
    print(f"requestqueued(): {stuff}")
    stuff = getrequest()
    print(f"getrequest(): {stuff}")
    stuff = getjingle()
    print(f"getjingle(): {stuff}")
    stuff = getsetting("notifytext")
    print(f"getsetting(notifytext): {stuff}")
    # setsetting('name', 'Skaianet Radio')
    closedb(commit=False)


if __name__ == '__main__':
    print("This is meant to be a library module; launching _test() instead")
    _test()
