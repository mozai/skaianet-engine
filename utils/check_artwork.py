#!/usr/bin/python3
" Validates and some updates to radio station track-art "
# Reads the /srv/radio/artwork dir to tell me what files aren't in the library
#  and what's in the library that isn't in this folder.
# If album art is missing, and it finds "track.jpg" copy it over and update the database

# TODO: validate_image could to more: corrupt data, weird width/height ratio

import argparse
import os
import os.path
import sys
sys.path.append('/srv/radio/engine')
import skaianet

# this is the 'no art found' image
NOARTFOUND_ART = "none.png"

# if we dive lower than this, we must've hit a loop
MAXDEPTH = 12

# holds config settings so I don't have to pass them everywhere
ARGS = None


def validate_image(fullpath):
    " saw a file on disk, check if it's bad or unused "
    isgood = True
    if os.path.islink(fullpath) and not os.path.exists(fullpath):
        print(f"-- WARN: broken symlink {fullpath}")
        isgood = False
    fsize = os.path.getsize(fullpath)
    if fsize < 1024:
        print(f"-- WARN: file is too small to be an image: {fullpath}")
        isgood = False
    elif fsize > 4 * 1048576:
        print(f"-- WARN: file is too big for albumart: {fullpath}")
        isgood = False
    return isgood


def fileswalk(startpath=skaianet.config["library.paths"]["artwork"]):
    " find all the files on disk, examine each "
    filescount = 0
    goodfiles = 0
    badfiles = 0
    nullart = os.path.join(
        skaianet.config["library.paths"]["artwork"], NOARTFOUND_ART)
    for fpath, _, files in os.walk(startpath, followlinks=True):
        if fpath.count(os.sep) > MAXDEPTH:
            raise Exception(
                f"-- EROR: library is too deep ({MAXDEPTH}); possible symlink loop")
        for fname in files:
            fullpath = os.path.join(fpath, fname)
            if fullpath == nullart:
                continue
            if fname[fname.rfind('.'):].lower() not in ('.jpg', '.jpeg', '.png', '.webm', '.avif',):
                print(f"-- WARN: unrecognized file: {fullpath}")
                continue
            filescount += 1
            try:
                if validate_image(fullpath):
                    goodfiles += 1
                else:
                    badfiles += 1
            except Exception as err:
                print(f"-- EROR: {fullpath}: {err}")
                continue
    if (goodfiles + badfiles) != filescount:
        print(
            f"-- EROR: saw {filescount} files but counted {goodfiles} good and {badfiles} bad")
    return goodfiles, badfiles


def update_artwork(songdata):
    " look for trackart, put it in-place "
    artworkpath = skaianet.config["library.paths"]["artwork"]
    musicpath = skaianet.config["library.paths"]["music"]
    songpath = os.path.join(musicpath, songdata["filepath"])
    oldfile, oldfile_mtime = None, 0
    if songdata["albumart"]:
        oldfile = os.path.join(artworkpath, songdata["albumart"])
        if os.path.exists(oldfile):
            oldfile_mtime = os.path.getmtime(oldfile)
        else:
            oldfile = None
    newfile, newfile_mtime = None, 0
    candidates = (songpath[:songpath.rfind('.')] + ".jpg",
                  songpath[:songpath.rfind('.')] + ".png",
                  os.path.join(songpath[:songpath.rfind('/')], "cover.jpg"),
                  os.path.join(songpath[:songpath.rfind('/')], "cover.png"),
                  )
    for i in candidates:
        if os.path.exists(i):
            newfile = i
            break
    # if not found:
    #  # attempt to get the art out of the mp3 file, via mutagen?
    if newfile:
        newfile_mtime = os.path.getmtime(newfile)
    albumart = None
    if newfile is None:
        if oldfile is None:
            albumart = None
        elif os.path.exists(oldfile):
            albumart = songdata["albumart"]
        else:
            albumart = None
    elif newfile_mtime <= oldfile_mtime:
        # file that's already there is newer
        albumart = songdata["albumart"]
    elif newfile_mtime > oldfile_mtime:
        # we found newer albumart
        fileext = newfile[newfile.rfind('.'):]
        albumart = f"""{songdata["id"]}{fileext}"""
        destination = os.path.join(artworkpath, albumart)
        if oldfile and os.path.exists(oldfile):
            if ARGS.commit:
                os.unlink(oldfile)
            else:
                print(f"""rm "{oldfile}" """)
        if os.path.exists(destination):
            if ARGS.commit:
                os.unlink(destination)
            else:
                print(f"""rm "{destination}" """)
        if ARGS.commit:
            os.symlink(newfile, destination)
        else:
            print(f"""ln -s "{newfile}" "{destination}" """)
    else:
        raise Exception("sanity failure")
    return albumart


def librarywalk():
    " look at what is mentioned in the database, and advise"
    goodcount = 0
    badcount = 0
    artworkpath = skaianet.config["library.paths"]["artwork"]
    songids = skaianet.listsongids()
    for sid in songids:
        row = skaianet.getsongbyid(sid)
        if not row:
            print(f"""-- EROR: bad songid {sid}""")
            badcount += 1
            continue
        oldalbumart = row["albumart"]
        newalbumart = update_artwork(row)  # returns shortname of new file
        if oldalbumart is None and newalbumart is None:
            if ARGS.warnmissing:
                print(f"""-- WARN: no art for song {row["id"]}""")
        elif newalbumart is None:
            print(
                f"""-- INFO: removing albumart {artworkpath}/{oldalbumart} for song {row["id"]}""")
            if ARGS.commit:
                skaianet.updatesong(row["id"], {"albumart": None})
            else:
                print(
                    f"""skaianet.updatesong({row["id"]}, {{"albumart": None}}""")
            badcount += 1
        elif newalbumart == row["albumart"]:
            goodcount += 1
        elif newalbumart != row["albumart"]:
            print(
                f"""-- INFO updating library with {{ id: {row["id"]}, albumart: {newalbumart} }}""")
            if ARGS.commit:
                skaianet.updatesong(row["id"], {"albumart": newalbumart})
            else:
                print(
                    f"""skaianet.updatesong({row["id"]}, {{"albumart": "{newalbumart}"}})""")
    return goodcount, badcount


def main():
    " Deploy cruxtruder "
    global ARGS
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true",
                        help="make changes (default is 'dryrun' report)")
    parser.add_argument("--warnmissing", action="store_true",
                        help="bark about songs without artwork")
    ARGS = parser.parse_args()

    print("-- checking the art files on-disk")
    good, bad = fileswalk()
    print(f"-- good: {good} bad: {bad}")
    print("-- checking the art mentioned in the database")
    good, bad = librarywalk()
    print(f"-- good: {good} bad: {bad}")


main()
