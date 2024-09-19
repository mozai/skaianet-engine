#!/usr/bin/python3
" Compare what's in the library paths and the database and barks about differences "

import argparse
import os
import os.path
import sys
sys.path.append('/srv/radio/engine')
import skaianet

# don't descend more than this many subfolders (in case of symlink loops)
MAXDEPTH = 8  # sanity check in case of symlink loops

# if a song's duration exceeds this, it shouldn't be in autoplay
AUTOPLAY_TOOSHORT = 30
AUTOPLAY_TOOLONG = 600
# if a song's duration exceeds this, it shouldn't be requestable (why is it here?)
REQUEST_TOOSHORT = AUTOPLAY_TOOSHORT * 0.667
REQUEST_TOOLONG = AUTOPLAY_TOOLONG * 1.5

# -----

# hold parameter switches so I don't have to pass it every time
ARGS = None


def log_info(msg):
    " saves typing "
    if sys.stdout.isatty():
        print(f"{msg}", file=sys.stdout)


def log_warn(msg):
    " saves typing "
    print(f"{msg}", file=sys.stderr)


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
    db_metadata = skaianet.getsongbypath(shortpath)
    db_metadata.pop("autoplay", None)
    db_metadata.pop("requestable", None)
    sid = db_metadata.get("id")
    success = True
    if db_metadata and not file_metadata:
        log_warn(f"WARN: song {shortpath} not on disk")
        if ARGS.commit:
            success = skaianet.rmsong(sid)
        else:
            print(f"""DBUG skaianet.rmsong({sid})""")
    elif file_metadata and not db_metadata:
        log_info(f"INFO: song {shortpath} not in library")
        # trackart is not processed here, its a different process for now
        if ARGS.commit:
            success = skaianet.addsong(fullpath)
        else:
            print(f"""DBUG skaianet.addsong({fullpath})""")
    else:
        # are they different? find out how
        # assume the file is always correct
        dbchanges = {}
        for k in ("title", "artist", "album", "length", "trackno", "release_date",):
            if file_metadata.get(k) != db_metadata.get(k):
                dbchanges[k] = file_metadata.get(k)
        if dbchanges:
            log_info(f"INFO: updating song {shortpath}")
            if ARGS.commit:
                success = skaianet.updatesong(sid, dbchanges)
            else:
                print(f"""DBUG skaianet.updatesong({sid}, {dbchanges})""")
    return success


def fileswalk(startpath=skaianet.config["library.paths"]["music"]):
    " examine the files on-disk, update library or carp "
    goodfiles = 0
    badfiles = 0
    for fpath, _, files in os.walk(startpath, followlinks=True):
        if fpath.count(os.sep) > MAXDEPTH:
            raise Exception(
                f"EROR: library is too deep ({MAXDEPTH}); possible symlink loop")
        for fname in sorted(files):
            fullpath = os.path.join(fpath, fname)
            if fname == ".skip_backup":
                # semaphore files used for maintenance
                continue
            if (fname[-4:] in ['.gif', '.jpg', '.pdf', '.png', '.txt']):
                continue
            if fname[-4:] in ['.nsf']:
                # Nintendo Sound Font, included in the Jailbreak album
                continue
            if (fname[-4:] not in ['.mp3', '.ogg']):
                log_warn(f"WARN: unrecognized file: {fullpath}")
                continue
            try:
                success = scrutinize_file(fullpath)
            except Exception as err:
                log_warn(f"EROR: {fullpath}: {err}")
                badfiles += 1
                continue
            if success:
                goodfiles += 1
            else:
                badfiles += 1
    return goodfiles, badfiles


def librarywalk():
    " look for files mentioned in the db that aren't on disk "
    # needs more sanity/validation while we're here?
    # like zero lengths, empty titles, non-URL website strings
    goodrows = 0
    badrows = 0
    songids = skaianet.listsongids()
    for sid in songids:
        row = skaianet.getsongbyid(sid)
        errors = []
        warnings = []
        for i in ("title", "length", "filepath"):
            if not row.get(i):
                errors.append(f"""song {row["id"]} missing {i}""")
        if row["length"] <= 0:
            errors.append(
                f"""song {row["id"]} file {row["filepath"]} has bad length {row["length"]}""")
        elif row["length"] >= AUTOPLAY_TOOLONG and (row["autoplay"]):
            warnings.append(
                f"""song {row["id"]} file {row["filepath"]} has autoplay and huge length {row["length"]}""")
            # should we set autoplay=false right away?
        elif row["length"] >= REQUEST_TOOLONG and (row["requestable"]):
            warnings.append(
                f"""song {row["id"]} file {row["filepath"]} has requestable and huge length {row["length"]}""")
        if '//' in row["filepath"]:
            warnings.append(
                f"""song {row["id"]} has doublesep in {row["filepath"]}""")
        if '../' in row["filepath"]:
            errors.append(
                f"""song {row["id"]} has '../' in {row["filepath"]}""")
        fullpath = os.path.join(
            skaianet.config["library.paths"]["music"], row["filepath"])
        if not os.path.exists(fullpath):
            errors.append(
                f"""song {row["id"]} file {row["filepath"]} is missing""")
        if warnings or errors:
            badrows += 1
        else:
            goodrows += 1
        for i in warnings:
            log_warn(f"WARN: {i}")
        for i in errors:
            log_warn(f"EROR: {i}")
        if errors:
            if ARGS.commit:
                skaianet.rmsong(row["id"])
            else:
                print(f"""DBUG skaianet.rmsong({row["id"]})""")
    return goodrows, badrows


def main():
    " Deploy cruxtruder "
    global ARGS
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true",
                        help="make changes (default is 'dryrun' report)")
    parser.add_argument("--warnmissing", action="store_true",
                        help="bark about songs without artwork")
    ARGS = parser.parse_args()

    log_info("INFO checking the files on-disk")
    good, bad = fileswalk()
    log_info(f"INFO filecount: good {good} bad {bad}")
    log_info("INFO checking the database rows")
    good, bad = librarywalk()
    log_info(f"INFO rowcount: good {good} bad {bad}")
    if not ARGS.commit:
        print("INFO launch again with '--commit' to write these changes")


main()
