#!/usr/bin/python3
" Compare what's in the library paths and the database and barks about differences "
# I should move most of these into engine/skaianet.py
#  but April 2024 I don't have time right now
#  and I should be moving all this into sqlite3 anyways

# TODO: all the 'print(sql)' statements should be replaced by calls
#  to skaianet class methods

#from collections import defaultdict
import os
import os.path
import sys
sys.path.append('/srv/radio/engine')
import skaianet

# don't descend more than this many subfolders (in case of symlink loops)
MAXDEPTH = 8  # sanity check in case of symlink loops

# if a song's duration exceeds this, it shouldn't be in autoplay
AUTOPLAY_TOOLONG = 600
# if a song's duration exceeds this, it shouldn't be requestable (why is it here?)
REQUEST_TOOLONG = AUTOPLAY_TOOLONG * 1.5

# what should match in library and in file metadata
#  "albumart" not here, gotta check that separately
SONG_FIELDS = [
    'title', 'artist', 'album', 'filepath', 'length', 'website',
    'release_date', 'trackno', 'autoplay', 'requestable',
]


# -----

def log_info(msg):
    " saves typing "
    if sys.stdout.isatty():
        print(f"{msg}", file=sys.stdout)


def log_warn(msg):
    " saves typing "
    print(f"{msg}", file=sys.stderr)


def insert_song(file_metadata):
    " found a new song on disk, add to db "
    file_metadata["autoplay"] = 1
    file_metadata["requestable"] = 1
    file_metadata.setdefault("length", 0)
    length = file_metadata["length"]
    if length < 30 or length > (8*60):
        file_metadata["autoplay"] = 0
        file_metadata["requestable"] = 0
    sql = "INSERT INTO library ("
    for i in sorted(file_metadata.keys()):
        if i not in SONG_FIELDS:
            continue
        sql += f"{i}, "
    sql = sql[:-2]
    sql += ") VALUES ("
    for i in sorted(file_metadata.keys()):
        if i not in SONG_FIELDS:
            continue
        if i in ("length", "autoplay", "requestable",):
            sql += f"{file_metadata[i]}, "
        elif file_metadata[i] is None or file_metadata[i] == "":
            sql += "null, "
        else:
            j = str(file_metadata[i]).replace('"', '\\"')
            sql += f"\"{j}\", "
    sql = sql[:-2]
    sql += ");"
    print(sql)


def update_song(idnum, file_metadata):
    " update the db with what I found on disk "
    sql = """UPDATE library SET """
    for i, j in file_metadata.items():
        if j is None:
            continue
        j = str(j)
        if i in ("length",):
            sql += f"{i} = {j}, "
        elif j is None:
            sql += f"{i} = null, "
        else:
            j = j.replace('\\', '\\\\').replace('"', '\\"')
            sql += f"{i} = \"{j}\", "
    sql = sql[:-2]
    sql += f" WHERE id = {idnum} ;"
    print(sql)


def rm_song(idnum):
    " Song's gone, purge it from the db "
    sql = f"""UPDATE library SET autoplay = 0, requestable = 0 WHERE id = {idnum};"""
    print(sql)


def fetch_song_by_filepath(shortpath):
    " I know where it is on disk, where is it in the db "
    cur = skaianet._DBCONN.cursor(dictionary=True)
    sql = "SELECT * FROM library WHERE filepath = %s"
    cur.execute(sql, (shortpath,))
    row = cur.fetchone()
    return row or {}


def scrutinize_file(fullpath):
    " compare one file to what's in the database"
    file_metadata = skaianet.getsongmeta(fullpath)
    shortpath = os.path.relpath(
        fullpath, skaianet.config["library.paths"]["music"])
    file_metadata["filepath"] = shortpath
    if file_metadata.get("title") is None:
        log_warn(f"EROR: song {shortpath} missing 'title' metadata; skipping")
        return False
    # "field album cannot be null" whoops.
    file_metadata.setdefault("album", "unknown")
    # "field artist cannot be null" whoops.
    file_metadata.setdefault("artist", "unknown")
    db_metadata = fetch_song_by_filepath(shortpath)
    db_metadata.pop("autoplay", None)
    db_metadata.pop("requestable", None)
    if db_metadata and not file_metadata:
        log_warn(f"WARN: song {shortpath} is missing")
        update_song(db_metadata["id"], {"autoplay": 0, "requestable": 0})
    elif file_metadata and not db_metadata:
        log_info(f"INFO: adding song {shortpath}")
        # trackart is not processed here, its a different process for now
        insert_song(file_metadata)
    else:
        # they're different, find out how
        dbchanges = {}
        filechanges = {}
        for k in SONG_FIELDS:
            if db_metadata.get(k) and (not file_metadata.get(k)):
                # keep whatever is in the database don't wipe it out please
                filechanges[k] = db_metadata[k]
            elif file_metadata.get(k) != db_metadata.get(k):
                dbchanges[k] = file_metadata.get(k)
        if dbchanges:
            log_info(f"INFO: updating song {shortpath}")
            update_song(db_metadata["id"], dbchanges)
        # to make it easier on myself, build an eyeD3 command
        #eyed3_params = ""
        #for i,j in filechanges.items():
        #    if j is None or j == "None":
        #        continue
        #    if i == 'album':
        #        eyed3_params += f" -A \"{j}\""
        #    elif i == 'artist':
        #        eyed3_params += f" -a \"{j}\""
        #    elif i == 'title':
        #        eyed3_params += f" -t \"{j}\""
        #    elif i == 'website':
        #        eyed3_params += f" --comment \"{j}\""
        #    else:
        #        eyed3_params += f" # {i}: \"{j}\""
        #if eyed3_params:
        #    log_info(f"INFO eyeD3 \"{shortpath}\" {eyed3_params}")
    return True


def fileswalk(startpath=skaianet.config["library.paths"]["music"]):
    " examine the files on-disk, update library or carp "
    filescount = 0
    for fpath, _, files in os.walk(startpath, followlinks=True):
        if fpath.count(os.sep) > MAXDEPTH:
            raise Exception(
                f"EROR: library is too deep ({MAXDEPTH}); possible symlink loop")
        for fname in sorted(files):
            fullpath = os.path.join(fpath, fname)
            if  fname == ".skip_backup":
                # semaphore files used for maintenance
                continue
            if (fname[-4:] in ['.gif', '.jpg', '.pdf', '.png', '.txt']):
                continue
            if  fname[-4:] in ['.nsf']:
                # Nintendo Sound Font, included in the Jailbreak album
                continue
            if (fname[-4:] not in ['.mp3', '.ogg']):
                log_warn(f"WARN: unrecognized file: {fullpath}")
                continue
            filescount += 1
            try:
                scrutinize_file(fullpath)
            except Exception as err:
                log_warn(f"EROR: {fullpath}: {err}")
                # raise
                continue
    return filescount


def librarywalk():
    " look for files mentioned in the db that aren't on disk "
    # needs more sanity/validation while we're here?
    # like zero lengths, empty titles, non-URL website strings
    rowscount = 0
    cur = skaianet._DBCONN.cursor(dictionary=True, buffered=True)
    cur.execute("SELECT * FROM library ORDER BY filepath ASC")
    for row in cur.fetchall():
        errors = []
        warnings = []
        for i in ("title", "length", "filepath"):
            if not row.get(i):
                errors.append(f"""song {row["id"]} missing {i}""")
        if row["length"] <= 0:
            errors.append(f"""song {row["id"]} file {row["filepath"]} has bad length {row["length"]}""")
        elif row["length"] >= AUTOPLAY_TOOLONG and (row["autoplay"]):
            warnings.append(f"""song {row["id"]} file {row["filepath"]} has autoplay and huge length {row["length"]}""")
            # should we set autoplay=false right away?
        elif row["length"] >= REQUEST_TOOLONG and (row["requestable"]):
            warnings.append(f"""song {row["id"]} file {row["filepath"]} has requestable and huge length {row["length"]}""")
        if '//' in row["filepath"]:
            warnings.append(f"""song {row["id"]} has doublesep in {row["filepath"]}""")
        if '../' in row["filepath"]:
            errors.append(f"""song {row["id"]} has '../' in {row["filepath"]}""")
        fullpath = os.path.join(
            skaianet.config["library.paths"]["music"], row["filepath"])
        if not os.path.exists(fullpath):
            errors.append(
                f"""song {row["id"]} file {row["filepath"]} is missing""")
        for i in warnings:
            log_warn(f"WARN: {i}")
        for i in errors:
            log_warn(f"EROR: {i}")
        if errors:
            rm_song(row["id"])
        rowscount += 1
    cur.close()
    return rowscount


def main():
    " Deploy cruxtruder "
    skaianet.initdb()
    log_info("-- checking the files on-disk")
    filecount = fileswalk()
    log_info("-- checking the database rows")
    rowcount = librarywalk()
    log_info(f"-- filecount: {filecount}, rowcount: {rowcount}")


main()
