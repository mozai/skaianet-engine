#!/usr/bin/env python3
" heart of skaianet python code "
###
# original version bears a copyright by George "Kitty" Burfeind
# and a statement that it is shared for public use as per
# the GNU General Public License v3 <http://www.gnu.org/licenses/>
# ... which means all derivative works must bear the same license for use.
###

from collections import defaultdict
import configparser
# import datetime  # was used by _dprint()
import os
import random
import re
import time
import sqlite3
import mutagen

__version__ = 20240828

# global var for the database connection
_DBCONN = None

# global for config settings
_CFGFILE = "/home/radio/engine/config.ini"

# access this in other scripts as skaianet.config
config = configparser.ConfigParser()

# if a song is bigger than this when you add it, don't set autoplay
SONGMAXLENGTH = 8 * 60

####################
# -- config file --
def loadconfig(cfgfile):
    " read config.ini so know where everything else is "
    global config
    config = configparser.ConfigParser()
    config.read(cfgfile)


def _checkconfig():
    # make sure the config settings are sane
    suggestions = []
    # TODO: do the checkconfig thing
    return suggestions

####################
# -- database as a whole --


def initdb(autocommit=True):
    " Initializes the database used for radio control. "
    global _DBCONN
    _DBCONN = sqlite3.connect(config["db.sqlite3"]["dbfile"], isolation_level=None)
    _DBCONN.row_factory = sqlite3.Row
    # _checkdbschema() 
    return _DBCONN


def closedb(commit=True):
    " Explict clean-up of open filehandles, net connections, flush disk caches "
    if commit:
        _DBCONN.commit()
    else:
        _DBCONN.rollback()   # .close() without .commit() should already do this
    _DBCONN.close()


def _checkdbschema():
    # make sure the tables are what we need
    suggestions = []
    # TODO: do the checkdbschema thing
    return suggestions


####################
# -- file-processing helpers

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
    for use in inserting/updating rows in the songs table
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
    elif path.endswith('.flac'):
        # TODO get meta for flac files
        raise Exception(f"cant do flac files yet: {path}")
    elif path.endswith('.wav'):
        # TODO get meta for wav files
        raise Exception(f"cant do wav files yet: {path}")
    else:
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


####################
# -- songs table --
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
    """ Add a song to the song library.
    Takes the path of an MP3 file, and then adds the path and metadata
    to the songs table for use in circulation or requests.
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
    if found:
        updatesong(found[0], songmeta)
    else:
        songmeta["autoplay"] = 1
        if songmeta["length"] >= SONGMAXLENGTH:
            songmeta["autoplay"] = 0
        elif songmeta["length"] <= 1:
            songmeta["autoplay"] = 0
        sql = "INSERT INTO songs " \
              "(title, artist, album, length, website, autplay, filepath) " \
              "VALUES (%(title)s, %(artist)s, %(album)s, %(length)s, %(website)s, %(autoplay)s, %(filepath)s)"
        cur.execute(sql, songmeta)
    cur.close()
    songmeta = getsongbypath(path)
    return songmeta.get("id")


def getrandomsong():
    """ fetch a song from the songs table that wasn't recently played
    """
    # actually returns the last-recently-played song of recentlimit + 1
    cur = _DBCONN.cursor()
    #recentlimit = config["engine"].get("recentlimit") or 20
    now = time.gmtime()
    if (now.tm_mon == 12 and now.tm_mday > 14 and random.random() < 0.334):
        # it's around christmas, play the christmas songs more often
        cur.execute("SELECT * FROM random_christmas_song")
    else:
        # cur.execute("SELECT l.* FROM (SELECT * FROM songs WHERE autoplay = 1 ORDER BY random() LIMIT %(range)s) l "
        #            "LEFT JOIN recent ON l.id = recent.songid ORDER BY recent.time ASC LIMIT 1",
        #            {'range': recentlimit + 1})
        # create or replace view `random_fresh_song` AS select * from songs where autoplay = 1 and not id in (select songid from recent where time > current_timestamp() - interval 1 hour) order by random() limit 1;
        # create or replace view `random_fresh_song` AS SELECT * FROM (SELECT * FROM songs WHERE autoplay = 1 ORDER BY random() LIMIT 20) AS subquery ORDER BY last_played ASC LIMIT 1;
        cur.execute("SELECT * FROM random_fresh_song")
    result = cur.fetchone()
    cur.close()
    assert result  # should never be None
    answer = dict(result)
    answer['reqname'] = ''
    answer['reqsrc'] = ''
    return answer


def getsongbyid(idnum):
    " get one song record "
    sql = "SELECT * FROM songs WHERE id = ?"
    cur = _DBCONN.cursor()
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
    if shortpath.startswith('/'):
        shortpath = shortpath[1:]
    cur = _DBCONN.cursor()
    sql = "SELECT * FROM songs WHERE filepath = ? or filepath = ? LIMIT 1"
    cur.execute(sql, (fullpath, shortpath,))
    found = cur.fetchone()
    cur.close()
    if not found:
        return None
    return found

def getsongbyartpath(fullpath):
    " found artwork, is it attached to a song? "
    # should I check if the file exists?
    fileext = fullpath[fullpath.rfind('.')+1:].lower()
    if fileext not in ('jpg', 'jpeg', 'webp', 'png', 'gif', 'avif'):
        return None
    librarypath = config["library.paths"].get("artwork")
    shortpath = fullpath.replace(librarypath, '')
    if shortpath.startswith('/'):
        shortpath = shortpath[1:]
    cur = _DBCONN.cursor()
    sql = "SELECT * FROM songs WHERE albumart = ? or albumart = ? LIMIT 1"
    cur.execute(sql, (fullpath, shortpath,))
    found = cur.fetchone()
    cur.close()
    if not found:
        return None  
    return found

def listsongids(autoplay=True, requestable=None):
    " puke up a long list of valid songids "
    # the way mysql works I can't make an ierator without loading ALL OF IT into memory at once >_<
    cur = _DBCONN.cursor()
    sql = "SELECT id from songs "
    wheres = []
    if autoplay is not None:
        if autoplay:
            wheres.append("autoplay = 1")
        else:
            wheres.append("autoplay = 0")
    if requestable is not None:
        if requestable:
            wheres.append("requestable = 1")
        else:
            wheres.append("requestable = 0")
    if wheres:
        sql += " WHERE " + " AND ".join(wheres)
    cur.execute(sql)
    found = list([row[0] for row in cur.fetchall()])
    cur.close()
    return found

def rmsong(idnum):
    " Remove a song from the songs table.  "
    removecursor = _DBCONN.cursor()
    # don't delete, because songs.id is a foreign key to other tables
    # removecursor.execute("DELETE FROM songs WHERE id=%(id)s", {'id': idnum})
    removecursor.execute(
        "UPDATE songs SET autoplay = 0, requestable = 0, length = NULL WHERE id=%(id)s", {'id': idnum})
    removecursor.close()


def updatesong(idnum, songdata):
    " update metadata on one song "
    # db agnostic way.  one song at a time please
    # ie. updatesong(413, {albumart: "413.jpg", length: 612})
    sql = "UPDATE songs SET "
    if 'length' in songdata:
        if songdata["length"] < 1:
            songdata["autoplay"] = 0
            songdata["requestable"] = 0
        elif songdata["length"] >= SONGMAXLENGTH:
            songdata["autoplay"] = 0
        del songdata["length"]
    params = [ ]
    for k,v in songdata.items():
        if k == "id":
            continue
        sql += f"{k} = ? , "
        params.append(v)
    if sql.endswith(", "):
        sql = sql[:-2]
    sql += " WHERE id = ? ;"
    params.append(idnum)
    cur = _DBCONN.cursor()
    cur.execute(sql, params)
    res = cur.rowcount
    cur.close()
    return res == 1


def _checksongstable():
    # for each row in songs table, do we have a file on disk?
    suggestions = []
    librarypath = config["library.paths"].get("music")
    cur = _DBCONN.cursor()
    cur.execute(
        "SELECT * FROM songs WHERE autoplay = 1 or requestable = 1 ORDER BY filepath;")
    for row in cur.fetchall():
        sid = row["id"]
        fullpath = os.path.join(librarypath, row['filepath'])
        if not os.path.isfile(fullpath):
            suggestions.append(f"""library: song {sid} missing file: {row["filepath"]}""")
        if not row["length"] > 1:
            suggestions.append(f"""library: song {sid} has bad length: {row["length"]}""")
        if not row["title"]:
            suggestions.append(f"""library: song {sid} missing title""")
        if not row["artist"]:
            suggestions.append(f"""library: song {sid} missing artist""")
    cur.close()
    return suggestions


def _checksongsfiles():
    # for each audio file on disk, do we have a row in songs table?
    suggestions = []
    librarypath = config["library.paths"].get("music")
    cur = _DBCONN.cursor()
    for root, _, files in os.walk(librarypath):
        for fname in files:
            if not (fname.endswith(".mp3") or fname.endswith(".ogg")):
                continue
            fullpath = os.path.join(root, fname)
            shortpath = fullpath.replace(librarypath, '')
            if shortpath.startswith('/'):
                shortpath = shortpath[1:]
            foundid = getsongbypath(shortpath)
            if foundid:
                continue
            suggestions.append(f"new file: {shortpath}")
    cur.close()
    return suggestions


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
    " got a file on disk, add it to the database "
    songmeta = getsongmeta(path)
    if songmeta is None:
        return None
    jinglepath = config["jingles"].get("path")
    if path.startswith(jinglepath):
        songmeta['filepath'] = path.replace(jinglepath, '')
    else:
        songmeta['filepath'] = path
    foundid = getjinglebypath(path)
    if foundid:
        return updatejingle(foundid, path)
    cur = _DBCONN.cursor()
    sql = "INSERT INTO jingles " \
          "(title, artist, length, website, filepath) " \
          "VALUES (%(title)s, %(artist)s, %(length)s, %(website)s, %(filepath)s)"
    cur.execute(sql, songmeta)
    cur.execute(
        "SELECT id FROM jingles WHERE filepath = %(filepath)s LIMIT 1", songmeta)
    row = cur.fetchone()
    cur.close()
    if not row:
        return None
    return row[0]


def listjingleids(autoplay=True):
    " puke up a long list of valid jingleids "
    # the way mysql works I can't make an ierator without loading ALL OF IT into memory at once >_<
    cur = _DBCONN.cursor()
    sql = "SELECT id from jingles "
    wheres = []
    if autoplay is not None:
        if autoplay:
            wheres.append("autoplay = 1")
        else:
            wheres.append("autoplay = 0")
    if wheres:
        sql += " WHERE " + " AND ".join(wheres)
    cur.execute(sql)
    found = list([row[0] for row in cur.fetchall()])
    cur.close()
    return found


def getrandomjingle():
    " fetch a new-ish station identification "
    cur = _DBCONN.cursor()
    cur.execute("SELECT * FROM (SELECT * FROM jingles WHERE autoplay = 1 ORDER BY random() LIMIT 5) AS subquery ORDER BY last_played ASC LIMIT 1;")
    result = cur.fetchone()
    cur.close()
    if result is None:
        return None
    answer = result.copy()
    answer['reqname'] = ''
    answer['reqsrc'] = ''
    return answer


def getjinglebyid(idnum):
    " fetch one jingle record "
    cur = _DBCONN.cursor()
    cur.execute("SELECT * FROM jingles WHERE id = ?", (idnum,))
    answer = cur.fetchone()
    cur.close()
    return answer


def getjinglebypath(fullpath):
    " return id# for the record for this file "
    if not (fullpath.endswith(".mp3") or fullpath.endswith(".ogg")):
        return None
    jinglepath = config["jingles"].get("path")
    shortpath = fullpath.replace(jinglepath, '')
    if shortpath.startswith('/'):
        shortpath = shortpath[1:]
    cur = _DBCONN.cursor()
    sql = "SELECT id FROM jingles WHERE filepath = ? or filepath = ? LIMIT 1"
    cur.execute(sql, (fullpath, shortpath,))
    found = cur.fetchall()
    cur.close()
    if not found:
        return None
    if len(found) > 1:
        # TODO: how should we report this error?
        pass
    return found[0]


def rmjingle(idnum):
    " Remove a jingle from play "
    cur = _DBCONN.cursor()
    sql = "UPDATE jingles SET autoplay = 0 WHERE id = ?"
    cur.execute(sql, (idnum,))
    cur.close()


def updatejingle(idnum, songdata):
    " update db record for one jingle "
    jinglefields = ("title", "artist", "filepath", "length", )
    values = []
    sql = "UPDATE jingles SET "
    for k in jinglefields:
        if k in songdata:
            sql += f"{k} = ?, "
            values.append(songdata[k])
    if sql.endswith(", "):
        sql = sql[:-2]
    sql += "WHERE id = ?;"
    values.append(idnum)
    cur = _DBCONN.cursor()
    cur.execute(sql, songdata)
    res = cur.rowcount
    cur.close()
    return res == 1


def _checkjinglestable():
    # for each row in jingles table, do we have a file on disk?
    suggestions = []
    jinglepath = config["jingles"].get("path")
    cur = _DBCONN.cursor()
    cur.execute(
        "SELECT id, filepath FROM jingles WHERE autoplay = 1 ORDER BY filepath;")
    for row in cur.fetchall():
        fullpath = os.path.join(jinglepath, row['filepath'])
        if os.path.isfile(fullpath):
            continue
        suggestions.append(
            f"""jingles: missing file: id:{row["id"]} filepath:{row["filepath"]}""")
    cur.close()
    return suggestions


def _checkjinglesfiles():
    # for each audio on disk, do we have a row in jingles table?
    suggestions = []
    jinglepath = config["jingles"].get("path")
    cur = _DBCONN.cursor()
    for root, _, files in os.walk(jinglepath):
        for fname in files:
            if not (fname.endswith(".mp3") or fname.endswith(".ogg")):
                continue
            fullpath = os.path.join(root, fname)
            shortpath = fullpath.replace(jinglepath, '')
            if shortpath.startswith('/'):
                shortpath = shortpath[1:]
            foundid = getjinglebypath(shortpath)
            if foundid:
                continue
            suggestions.append(f"new jingle: {shortpath}")
    cur.close()
    return suggestions


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
def setplaying(songid, reqname='', reqsrc='', listeners=0, jingle=False):
    """ Adds a song to the recently played database.
    This is assuming that this function is called when the song starts
    playing so that the timing can be accurate for linked functions.
    Takes arguments of the songs DB number, title, album, artist,
    length in seconds, and optionally, the person requesting the song,
    and optiononally, how many people are listening right now.
    """
    cur = _DBCONN.cursor()
    if jingle:
        sql = "UPDATE jingles SET last_played = current_timestamp WHERE id = ?"
        cur.execute(sql, (songid, ))
    else:
        sql = "INSERT INTO recent (songid, reqname, reqsrc, time, listeners) " \
            "VALUES (?, ?, ?, current_timestamp, ? )"
        data = (songid, reqname, reqsrc, listeners,)
        cur.execute(sql, data)
        sql = "UPDATE songs SET last_played = current_timestamp WHERE id = ?"
        cur.execute(sql, (songid,))
    cur.close()


def getplaying():
    " returns object that describes curently-playing song "
    cur = _DBCONN.cursor()
    cur.execute("SELECT * FROM current_song;")  # uses the view
    result = cur.fetchone()
    cur.close()
    assert result  # should never be None
    answer = dict(result)
    return answer


def _checkrecenttable():
    # tell me about the mess
    suggestions = []
    # TODO: what do we do to validate the recents table?
    cur = _DBCONN.cursor()
    cur.execute("SELECT sum(1), max(julianday() - julianday(time)) FROM recent;")
    row = cur.fetchone()
    if row[0] < (128 * 1024):
        suggestions.append(
            f"recent: do you need {row[0]} rows in the recent table?")
    if row[1] > 366:
        suggestions.append(
            f"recent: do you need {row[1]}>365 days of history?")
    return suggestions


####################
# -- requests table --
# should be:
#   id: int, primary key -- probably unused
#   reqid: int  -- foreign key to songs.id
#   reqname: varchar
#   reqsrc: varchar
#   override: bool  -- unused

def addrequest(songid, reqname, reqsrc):
    " user wants to hear a song "
    cur = _DBCONN.cursor()
    sql = "INSERT INTO requests (songid, reqname, reqsrc) VALUES (?, ?, ?)"
    cur.execute(sql, (songid, reqname, reqsrc,))
    cur.execute("SELECT * FROM requests ORDER BY id DESC")
    found = cur.fetchone()
    cur.close()
    if found:
        return found[0]
    return None

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
def getrequest(pop=True):
    " pops a request off the head of the queue "
    answer = None
    while answer is None:
        cur = _DBCONN.cursor()
        cur.execute(
            "SELECT id, songid, reqname, reqsrc FROM requests ORDER BY id ASC LIMIT 1")
        reqdata = cur.fetchone()
        if reqdata is None:
            break
        if pop:
            cur.execute("DELETE FROM requests WHERE id = ?", (reqdata['id'],))
        cur.execute(
            "SELECT id, filepath, title, artist, album, length, "
            "website FROM songs WHERE id = ? and requestable = 1 LIMIT 1",
            (reqdata['songid'],))
        libdata = cur.fetchone()
        if libdata:
            answer = dict(libdata)
            answer['reqname'] = reqdata['reqname']
            answer['reqsrc'] = reqdata['reqsrc']
    return answer


def _checkrequeststable():
    # tell me about the mess
    suggestions = []
    # dunno what to do here, since it'll be empty most of the time
    # check for rows where reqid doesn't match any songs.id ?
    return suggestions


####################
# -- settings table --
# should be:
#   name: varchar, primary key
#   value: varchar

def getsetting(name):
    " update the entries in table settings "
    cur = _DBCONN.cursor()
    sql = "SELECT value FROM settings WHERE name = ?"
    cur.execute(sql, (name,))
    row = cur.fetchone()
    cur.close()
    answer = row[0]
    return answer


def setsetting(name, value):
    " update the entries in table settings "
    cur = _DBCONN.cursor()
    if not getsetting(name):
        cur.execute("INSERT INTO settings (name, value) VALUES (?, ?)", (name, value,))
    else:
        cur.execute("UPDATE settings SET value = ? WHERE name = ?", (value, name,))
    cur.close()


def listsettings():
    " maybe I want to know all possible getsettings "
    cur = _DBCONN.cursor()
    cur.execute("SELECT name FROM settings ORDER BY name")
    answer = cur.fetchall()
    return [i[0] for i in answer]


def _checksettingstable():
    " verify we have the settings we need and they arent crap "
    suggestions = []
    for i in ("stationname",):
        j = getsetting(i)
        if not j:
            suggestions.append(f"bad value for setting {i}: \"{j}\"")
    for i in ("artworkurl", "jingleurl", "musicurl",):
        j = getsetting(i)
        if j and not (j.startswith("//") or j.startswith("https://") or j.startwith("http://")):
            suggestions.append(f"settings: bad value for setting {i}: \"{j}\"")
    j = int(getsetting("requestlimit"))
    if j < 1 or j > 5:
        suggestions.append(
            f"settings: bad value for setting requestlimit: \"{j}\"")
    j = getsetting("notifytext")
    if ('<' in j) or ('\n' in j) or (len(j) > 63):
        suggestions.append(
            f"settings: bad value for setting notifytext: \"{j}\"")
    return suggestions


####################
# -- songtags table --
# should be:
#   songid: int --  foreign key to songs.id
#   tag: varchar(63)

def _checktagstable():
    " verify every tag has a song "
    suggestions = []
    cur = _DBCONN.cursor()
    cur.execute("SELECT t.songid as songid, t.tag as tag, s.id as sid FROM songtags t LEFT JOIN songs s on t.songid = s.id")
    answer = cur.fetchall()
    for i in answer:
        if i["sid"] is None:
            suggestions.append(f"""tags: absent song for tag ({i["songid"]}, {i["tag"]})""")
        if " " in i["tag"] or i["tag"] != i["tag"].lower():
            suggestions.append(f"""tags: tag must be lower nonspaces ({i["songid"]}, {i["tag"]})""")
    return suggestions


####################

def listdbproblems():
    " launch the tests, tell me what you got; true on problems "
    problems = []
    problems.extend(_checkdbschema())
    problems.extend(_checksongstable())
    problems.extend(_checkjinglestable())
    problems.extend(_checkrequeststable())
    problems.extend(_checksettingstable())
    return problems


def listfileproblems():
    " launch the tests, tell me what you found; true on problems "
    problems = []
    problems.extend(_checksongsfiles())
    problems.extend(_checkjinglesfiles())
    return problems


####################

# do these on load, in case someone forgets
loadconfig(_CFGFILE)
initdb(autocommit=True)

if __name__ == '__main__':
    print("This is meant to be a library module; launching tests instead")
    print("*** testing skaianet module")
    config["engine"]["debug"] = "true"
    # turn off database commits so we can test the set*() methods
    initdb(autocommit=False)

    print("-- test songs table ---")
    # songs table
    # addsong(filepath)
    stuff = listsongids()
    print(f"listsongids(): {len(stuff)} rows with autoplay=True")
    testsong = getrandomsong()
    print(f"getrandomsong(): {testsong}")
    print(f"""getsongbyid({testsong["id"]}): {getsongbyid(testsong["id"])}""")
    filepath = os.path.join(
        config["library.paths"]["music"], testsong['filepath'])
    print(f"getsongbypath({filepath}): {getsongbypath(filepath)}")
    # rmsong(testsong["id"])

    # helpers
    print("-- test helpers ---")
    print(f"getsongmeta({filepath}): {getsongmeta(filepath)}")

    # jingles
    print("-- test jingles ---")
    stuff = listjingleids()
    print(f"listjingleids(): {len(stuff)} rows with autoplay=True")
    stuff = getrandomjingle()
    print(f"getrandomjingle(): {stuff}")

    # requests table
    print("-- test requests ---")
    print(f"""addrequest({testsong["id"]}, Testuser, 127.0.0.1): {addrequest(testsong["id"], "Testuser", "127.0.0.1")}""")
    print(f"requestqueued(): {requestqueued()}")
    #print(f"getrequest(): {getrequest()}")

    print("-- test settings ---")
    print(f"""listsettings(): {listsettings()}""")
    stuff = getsetting("notifytext")
    print(f"""getsetting(notifytext): {stuff}""")
    #print(f"""setsetting('notifytext', {stuff}) : {setsetting('notifytext', stuff)}""")

    # maintenance
    print("-- listdbproblems() ---")
    suggs = listdbproblems()
    print(f"suggestion count: {len(suggs)}")
    if suggs:
        print("- " + "\n- ".join(suggs))
    print("-- listfileproblems() ---")
    suggs = listfileproblems()
    print(f"suggestion count: {len(suggs)}")
    if suggs:
        print("- " + "\n- ".join(suggs))

    # close without writing
    closedb(commit=False)
