#!/usr/bin/env python
" for ezstream, fetch metadata about currently-playing song "
# TODO: rewrite this in something faster like golang
#       but then I'm not using skaianet.py anymore, hrm.

# from `man ezstream`, chapter "SCRIPTING"
# Metadata Programs
# -   The program must not return anything (just a newline character is
#     okay) if it is called by ezstream with  a command line argument
#     that the program does not support.
# -   When called without command line arguments, the program should
#     return a complete string that should be used for metadata.
# -   When called with the command line argument "artist", the program
#     should return only the artist information of the metadata.  (Optional.)
# -   When called with the command line argument "title", the program
#     should return only the title information of the metadata.  (Optional.)
# -   The supplied metadata must be encoded in UTF-8.

import sys
sys.path.append('/srv/radio/engine')
import skaianet

def getplaying():
    " saves typing "
    skaianet.initdb()
    songinfo = skaianet.getplaying()
    skaianet.closedb()
    return songinfo

def main():
    " :33 < *ac writes captions on her shipping wall* "
    if len(sys.argv) == 2:
        if sys.argv[1] in ("title", "artist"):
            i = getplaying()
            print(f"""{i[sys.argv[1]]}""")
        else:
            print("")
    elif len(sys.argv) == 1:
        i = getplaying()
        print(f"""{i["title"]} - {i["artist"]}""")
    else:
        print("")

main()
