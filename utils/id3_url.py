#!/usr/bin/env python
""" This sets the comment field for mp3 files in a least-broken way.
To be used for inserting website urls into the mp3 files for the radio
station as the comment field that will be visible to graphical mp3 players
"""
# it is such a clusterfuck.  gui tools ignore the W*** tags
# id3v2 just fails, and if the id3 tag is v2.4 it acts like nothing's there
# mid3v2 will extra characters, make it invalid as a url.
# eyeD3 and mid3v2 will truncate strings that have ':' in them
# eyeD3 writes comments to COMM:eng but gui tools only read COMM:XXX
# eyeD3 also writes the entire text in the description part of a W***
#   tag not just the url part
#   ie. "WCOM:https://example.com": "https://example.com"
# gui tools only read/write from tags that have 'XXX' as the language and
#   an empty string as the description field

import mutagen
import mutagen.id3
import sys
sys.path.append('/srv/radio/engine')
import skaianet
COMM = mutagen.id3.COMM

fnames = []
if len(sys.argv) >= 3:
    inurl = sys.argv[1]
    fnames = sys.argv[2:]
elif len(sys.argv) == 2:
    inurl = None
    fnames = sys.argv[1:]
if not fnames:
    print("Usage: {} filename.mp3".format(sys.argv[0]))
    print("   gets the comment in this file")
    print("Usage: {} \"url\" filename.mp3 [filename2.mp3 filename3.mp3 ...]".format(sys.argv[0]))
    print("   sets the comments in this file / these files")
    sys.exit(1)

for fname in fnames:
    m = mutagen.File(fname)
    print(fname + ": ")
    oldurl = skaianet._extract_a_url_from_mutagen_mp3(m)
    print("  current website guess: " + str(oldurl))
    if inurl:
        m['COMM::XXX'] = COMM(encoding=3, lang='XXX', desc='', text=inurl)
        m.save()
        newurl = skaianet._extract_a_url_from_mutagen_mp3(m)
        print("  new website guess: " + str(newurl))
