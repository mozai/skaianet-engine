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
#import datetime  # was used by _dprint()
import os
import random
import re
import time
import mutagen
import mysql.connector
__version__ = 20240808  # Hello Vriska

# need some globals for the record structs
library_fields = [
    'id', 'title', 'artist', 'album', 'filepath', 'albumart',
    'autoplay', 'requestable', 'length', 'website',
    'last_played', 'release_date', 'trackno'
]
#jingle_fields = [ 
#    'id', 'title', 'artist', 'filepath', 'albumart',
#    'autoplay', 'length', 'last_played'
#]
requests_fields = [
    'id', 'reqid', 'reqname', 'reqsrc', 'override'
]
#settings_fields = [ 'name', 'value' ]

# global var for the database connection
_DBCONN = None

# global for config settings
_CFGFILE = "/home/radio/engine/config.ini"
config = configparser.ConfigParser()


####################
# -- init --
def loadconfig(cfgfile):
    global config
    config = configparser.ConfigParser()
    config.read(cfgfile)

def initdb(autocommit=True):
    """ Initializes the database used for radio control.
    Must be called on it's own at least once before anything that
    calls the database is used.
    """
    # TODO: don't expect the user to call initdb just DO IT on module load
    global _DBCONN
    _DBCONN = mysql.connector.connect(user=config["db.mysql"]["dbuser"],
                                      password=config["db.mysql"]["dbpass"],
                                      database=config["db.mysql"]["dbname"],
                                      autocommit=autocommit)
    # TODO: should verify schema to make sure it matches expectations
    return _DBCONN

def closedb(commit=True):
    """ Ensures all changes are saved before closing the database.
    Should be called only when all DB actions are done.
    """
    if commit:
        _DBCONN.commit()
    else:
        _DBCONN.rollback()   # .close() without .commit() should already do this
    _DBCONN.close()


####################
# -- library table --
# should be 
#   id: int, unique, primary key
#   title: varchar, notnull
#   artist: varchar
#   album: varchar
#   release_date: varchar
#   trackno: int
#   website: varchar
#   length: int, notnull
#   filepath: varchar, notnull
#   albumart: varchar
#   autoplay: bool
#   requestable: bool
#   last_played: datetime
def addsong(path):
    """ Add a song to the library.
    Takes the path of an MP3 file, and then adds the path and metadata
    to the library database for use in circulation or requests.
    """
    songmeta = getsongmeta(path)
    if songmeta is None:
        return None
    librarypath = config["library.paths"].get("music")
    if path.startswith(librarypath):
        songmeta['filepath'] = path.replace(librarypath, '')
    else:
        songmeta['filepath'] = path
    cur = _DBCONN.cursor()
    cur.execute(
        "SELECT id FROM library WHERE filepath = %(filepath)s LIMIT 1", songmeta)
    found = cur.fetchone()
    cur.close()
    cur = _DBCONN.cursor()
    if found:
        songmeta['id'] = found[0]
        sql = "UPDATE library SET album = %(album)s, " \
              "artist = %(artist)s, length = %(length)s, " \
              "title = %(title)s, website = %(website)s " \
              "WHERE id = %(id)s"
    else:
        sql = "INSERT INTO library " \
              "(title, artist, album, length, website, filepath) " \
              "VALUES (%(title)s, %(artist)s, %(album)s, %(length)s, %(website)s, %(filepath)s)"
    cur.execute(sql, songmeta)
    cur.close()
    cur = _DBCONN.cursor()
    cur.execute(
        "SELECT id FROM library WHERE filepath = %(filepath)s LIMIT 1", songmeta)
    row = cur.fetchone()
    cur.close()
    return row[0]  # library.id of the new/updated row


def getrandomsong():
    """ fetch a song from the library that wasn't recently played
    """
    # TODO: should use a stored procedure or view in sql since this darn thing
    #   needs to be restarted every time I want to make a change >_<

    # actually returns the last-recently-played song of recentlimit + 1
    cur = _DBCONN.cursor(buffered=True, dictionary=True)
    #recentlimit = config["engine"].get("recentlimit") or 20
    now = time.gmtime()
    if (now.tm_mon == 12 and now.tm_mday > 14 and random.random() < 0.334):
        # it's around christmas, play the christmas songs more often
        # TODO: have a 'christmas' tag on songs, or have a christmas sublist
        # create or replace view random_christmas_song AS select * from library where autoplay = 1 AND ((album in ("Homestuck for the Holidays", "Gristmas Carols") or (title like "%ristmas%") or (title like "Carol%") or (title = "Home" and artist = "PhemieC"))) order by rand() limit 1;
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
    return answer


def getsongbyid(idnum):
    " get one song record "
    sql = "SELECT * FROM library WHERE id = %s"
    cur = _DBCONN.cursor(dictionary=True)
    cur.execute(sql, (idnum,))
    answer = cur.fetchone()
    cur.close()
    return answer

def getsongbypath(fullpath):
    " find library entry matching file on disk "
    if not (fullpath.endswith(".mp3") or fullpath.endswith(".ogg")):
        return None
    librarypath = config["library.paths"].get("music")
    shortpath = fullpath.replace(librarypath, '')
    cur = _DBCONN.cursor()
    sql = "SELECT id FROM library WHERE filepath = %(fullpath)s or filepath = %(shortpath)s LIMIT 1"
    cur.execute(sql, {'fullpath': fullpath, 'shortpath': shortpath})
    found = cur.fetchall()
    cur.close()
    if not found:
        return None
    if len(found) > 1:
        # TODO: how should we report this error?
        pass
    return found[0]


def rmsong(idnum):
    " Remove a song from the library.  "
    removecursor = _DBCONN.cursor()
    # don't delete, because library.id is a foreign key to other tables
    # removecursor.execute("DELETE FROM library WHERE id=%(id)s", {'id': idnum})
    removecursor.execute(
        "UPDATE library SET autoplay = 0, requestable = 0, length = NULL WHERE id=%(id)s", {'id': idnum})
    removecursor.close()


def updatesong(idnum, songdata):
    " update metadata on one song "
    # db agnostic way.  one song at a time please
    # ie. updatesong(413, {albumart: "413.jpg", length: 612})
    # TODO: do some data validation
    sql = "UPDATE library SET "
    for k in songdata.keys():
        if k == "id":
            continue
        sql += f"{k} = %({k})s, "
    if sql.endswith(", "):
        sql = sql[:-2]
    sql += f" WHERE id = {idnum};"
    cur = _DBCONN.cursor()
    cur.execute(sql, songdata)
    res = cur.rowcount
    cur.close()
    return res == 1


####################
# -- maintenance/upkeep
def _extract_a_url_from_mutagen_mp3(mutagenf):
    # what a clusterfuck
    # ref http://www.unixgods.org/Ruby/ID3/docs/ID3_comparison.html
    # can't just use framename, because it could be 'WCOM:full_url' or
    # 'WXXX:' or 'WXXX:None' or 'COMM::eng' or 'COMM::ENG' or 'COMM::XXX'
    # or ....
    # and!  it will read id3 tags before id3v2 tags which means truncated comments
    diggy = re.compile(r'''((f|ht)tps?://[^ }"',]+)''', re.S | re.I)
    # first try the most likely place
    matchobj = diggy.search(str(mutagenf.tags.get('COMM::XXX')))
    if matchobj:
        return matchobj.group(1)
    # then try everywhere else: W ones are supposed to be URLs but there's so many
    frames = []
    frames.extend(
        sorted([i for i in mutagenf.tags.keys() if i.startswith('WXXX')]))
    frames.extend(
        sorted([i for i in mutagenf.tags.keys() if i.startswith('W')]))
    frames.extend(
        sorted([i for i in mutagenf.tags.keys() if i.startswith('COM')]))
    frames.extend(
        sorted([i for i in mutagenf.tags.keys() if i.startswith('TXX')]))
    for frame in frames:
        matchobj = diggy.search(str(mutagenf.tags[frame]))
        if matchobj:
            return matchobj.group(1)
    return None


def _extract_a_url_from_mutagen_ogg(mutagenf):
    diggy = re.compile(r'((f|ht)tps?://[^\s},"\']+)', re.S | re.I)
    for i in ('contact', 'comment', 'description', 'license'):
        for j in mutagenf.get(i, []):
            matchobj = diggy.search(j)
            if matchobj:
                return matchobj.group(1)
    return None


def _get_best_date(mutagenf):
    # Jesus murphy, they did not make things easy
    # ID2.2 = TDA, TYE (year only), TOR (year only), TRD,
    # ID2.3 = TYER (year only), TORY (year only), TRDA,
    # ID2.4 = TDLR TDOR TDRC
    answer = None
    for i in ('TDRL', 'TDAT', 'TDA', 'TDOR', 'TDRC', 'TORY', 'TYE', 'TOR', 'TRDA', 'TRD', 'TYER', 'TYE',):
        answer = mutagenf.tags.get(i)
        if answer is not None:
            break
    return answer


def getsongmeta(path):
    """ given filename, return metadata from that file
    for use in inserting/updating rows in the library table
    """
    # provides 'None' for missing tags, eqiv. of NULL in database
    answer = defaultdict(lambda: None)
    if path.endswith('mp3'):
        i = mutagen.File(path)
        # list of keys at http://id3.org/id3v2.3.0
        # better list http://www.unixgods.org/Ruby/ID3/docs/ID3_comparison.html
        answer['album'] = str(i.get('TALB', ''))
        answer['artist'] = str(i.get('TPE1', ''))
        answer['title'] = str(i.get('TIT2', ''))
        answer['length'] = round(i.info.length)
        answer['track'] = int(str(i.get('TRCK', '0')))
        answer['release_date'] = _get_best_date(i)
        answer['website'] = _extract_a_url_from_mutagen_mp3(i)
    elif path.endswith('.ogg'):
        # https://www.xiph.org/vorbis/doc/v-comment.html
        # here are there suggestions, and they can appear multiple times
        # TITLE, VERSION, ALBUM, TRACKNUMBER, ARTIST, PERFORMER,
        # COPYRIGHT, LICENSE, ORGANIZATION, DESCRIPTION, GENRE, DATE,
        # LOCATION, CONTACT, ISRC
        i = mutagen.File(path)
        answer['album'] = str(i.get('ALBUM'))
        answer['artist'] = str(i.get('ARTIST', ''))
        answer['title'] = str(i.get('TITLE', ''))
        answer['length'] = round(i.info.length)
        answer['track'] = int(str(i.get('TRACKNUMBER', '0')))
        answer['release_date'] = str(i.get('DATE'))
        answer['website'] = _extract_a_url_from_mutagen_ogg(i)
    else:
        # TODO: how to analyze other audio/* file types
        raise Exception(f"unrecognized file type: {path}")
    for i in list(answer.keys()):
        if answer[i] == '':
            del answer[i]
    if answer.get('release_date') is not None:
        j = str(answer.get('release_date'))
        if ' ' in j:
            j = j[:j.index(' ')]
        if ',' in j:
            j = j[:j.index(',')]
        answer['release_date'] = j
    answer['filename'] = os.path.basename(path)
    answer['filepath'] = path
    return answer


def _checklibraryfiles(commit=False):
    # for each file on disk, do we have a row in library table?
    suggestions = []
    librarypath = config["library.paths"].get("music")
    for root, _, files in os.walk(librarypath):
        for fname in files:
            if not (fname.endswith(".mp3") or fname.endswith(".ogg")):
                continue
            fullpath = os.path.join(root, fname)
            shortpath = fullpath.replace(librarypath, '')
            cur = _DBCONN.cursor()
            sql = "SELECT id FROM library WHERE filepath = %(fullpath)s or filepath = %(shortpath)s LIMIT 1"
            cur.execute(sql, {'fullpath': fullpath, 'shortpath': shortpath})
            found = cur.fetchall()
            cur.close()
            if found:
                continue
            suggestions.append(f"new file: {shortpath}")
            if commit:
                addsong(fullpath)
    return suggestions


def _checklibrarytable(commit=False):
    # for each row in library table, do we have a file on disk?
    suggestions = []
    mp3libcursor = _DBCONN.cursor(dictionary=True)
    mp3libcursor.execute(
        "SELECT id, filepath FROM library WHERE autoplay = 1 or requestable = 1 ORDER BY filepath;")
    librarypath = config["library.paths"].get("music")
    for row in mp3libcursor.fetchall():
        fullpath = os.path.join(librarypath, row['filepath'])
        if os.path.isfile(fullpath):
            continue
        suggestions.append(f"missing file: {fullpath}")
        if commit:
            rmsong(row['id'])
    mp3libcursor.close()
    return suggestions


def checkdb(commit=False):
    """ Check the database against the song library for consistency,
    and vice-versa.  Returns suggested changes. set commit = True to
    implement suggested changes.
    """
    answer = []
    suggestions = _checklibraryfiles(commit)
    answer.extend(suggestions)
    suggestions = _checklibrarytable(commit)
    answer.extend(suggestions)
    return sorted(answer)


####################
# -- recent table --
# should be:
#   id: int, primary key -- probably unused
#   songid: int
#   jingleid: int
#   reqname: varchar
#   reqsrc: varchar
#   time: datetime
#   listeners: int
def setplaying(songid, title, artist, album, length,
               reqname='', reqsrc='', listeners=0, jingle=False):
    """ Adds a song to the recently played database.
    This is assuming that this function is called when the song starts
    playing so that the timing can be accurate for linked functions.
    Takes arguments of the songs DB number, title, album, artist,
    length in seconds, and optionally, the person requesting the song,
    and optiononally, how many people are listening right now.
    """
    # TODO: parameter should just be songid, requestid=None, listeners=0)
    setcursor = _DBCONN.cursor()
    if jingle:
        query = "UPDATE jingles SET last_played = CURRENT_TIMESTAMP() WHERE id = %(songid)s"
        data = {'songid': songid}
        setcursor.execute(query, data)
    else:
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
    " returns object that describes curently-playing song "
    cur = _DBCONN.cursor(dictionary=True)
    cur.execute("SELECT * FROM recent ORDER BY time DESC LIMIT 1")
    result = cur.fetchone()
    cur.close()
    assert result  # should never be None
    answer = result.copy()
    return answer


####################
# -- requests table --
# should be:
#   id: int, primary key -- probably unused
#   reqid: int  -- foreign key to library.id
#   reqname: varchar
#   reqsrc: varchar
#   override: bool  -- unused

def addrequest():
    " user wants to hear a song "
    # TODO: the php writes directly to the table, but
    #   we should have the procedure defined here too
    raise Exception("not implemented yet")


# TODO: replace this with if(getrequest())
def requestqueued():
    " Checks if there is a request waiting to be processed. "
    # Takes no arguments, returns True or False.
    # TODO: do we need this? or can getrequest() just return None ?
    cur = _DBCONN.cursor()
    cur.execute('SELECT id FROM requests LIMIT 1')
    found = cur.fetchone()
    cur.close()
    return found is not None


# TODO: should rename this to poprequest or shiftrequest so we know we're writing
def getrequest():
    " pops a request off the head of the queue "
    answer = None
    while answer is None:
        reqcursor = _DBCONN.cursor(dictionary=True)
        reqcursor.execute(
            "SELECT id, reqid, reqname, reqsrc FROM requests LIMIT 1")
        reqdata = reqcursor.fetchone()
        reqcursor.close()
        if reqdata is None:
            break
        reqrmcursor = _DBCONN.cursor()
        reqrmcursor.execute("DELETE FROM requests WHERE id=%(id)s",
                            {'id': reqdata['id']})
        reqrmcursor.close()
        libcursor = _DBCONN.cursor(dictionary=True)
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
    return answer


####################
# -- library_christmas table
# should be:
#   songid: int, primary key

# no functions in the engine; you make this table by hand,
#   and it's used by the getrandomson() above

####################
# -- jingles table --
# should be:
#   id: int, primary key
#   title: varchar, not null
#   artist: varchar
#   filepath: varchart, not null
#   length: int, not null
#   website: varchar
#   albumart: varchar
#   autoplay: bool
#   last_played: datetime

def addjingle(path):
    pass
def getrandomjingle():
    pass
def getjinglebyid(idnum):
    pass
def getjinglebypath(fullpath):
    pass
def rmjingle(idnum):
    pass
def updatejingle(idnum, songdata):
    pass


####################
# -- settings table --
# should be:
#   name: varchar, primary key
#   value: varchar

def getsetting(name):
    " update the entries in table settings "
    cur = _DBCONN.cursor(buffered=True)
    sql = "SELECT value FROM settings WHERE name=%(name)s"
    data = {'name': name}
    cur.execute(sql, data)
    row = cur.fetchone()
    cur.close()
    answer = row[0]
    return answer


def setsetting(name, value):
    " update the entries in table settings "
    reqcursor = _DBCONN.cursor()
    reqcursor.execute("INSERT INTO settings (name, value) VALUES (%(n)s, %(v)s) ON DUPLICATE KEY UPDATE value = %(v)s", {
                      'n': name, 'v': value})
    reqcursor.close()

def listsettings():
    " maybe I want to know all possible getsettings "
    cur = _DBCONN.cursor()
    cur.execute("SELECT name FROM settings ORDER BY name")
    answer = cur.fetchall()
    return answer


####################

# do these on load, in case the forgets
loadconfig(_CFGFILE)
initdb(True)

if __name__ == '__main__':
    print("This is meant to be a library module; launching tests instead")
    print("*** testing skaianet module")
    config["engine"]["debug"] = "true"
    # turn off database commits so we can test the set*() methods
    initdb(autocommit=False)

    # library table
    # addsong(filepath)
    stuff = getrandomsong()
    print(f"getrandomsong(): {stuff}")
    print(f"""getsongbyid({stuff["id"]}): {getsongbyid(stuff["id"])}""")
    filepath = os.path.join(config["library.paths"]["music"], stuff['filepath'])
    print(f"getsongbypath({filepath}): {getsongbypath(filepath)}")
    # rmsong(stuff["id"])

    # maintenance
    print(f"getsongmeta({filepath}): {getsongmeta(filepath)}")

    #print(f"getrandomjingle(): {getrandomjingle()}")

    # requests table
    print(f"""addrequest({stuff["id"]}): {addrequest(stuff["id"])}""")
    print(f"requestqueued(): {requestqueued()}")
    #print(f"getrequest(): {getrequest()}")


    print(f"""listsettings(): {listsettings()}""")
    stuff = getsetting("notifytext")
    print(f"""getsetting(notifytext): {stuff}""")
    #print(f"""setsetting('notifytext', {stuff}) : {setsetting('notifytext', stuff)}""")

    # maintenance
    suggestions = checkdb(commit=False)
    print(f"checkdb() suggestion count: {len(suggestions)}")
    print("- " + "\n- ".join(suggestions))

    # close without writing
    closedb(commit=False)
