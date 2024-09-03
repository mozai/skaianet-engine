#!/usr/bin/python3
" Sanity check on the settings table "
# this seems small but I'm being constantly interrupted
# can't even write one comment without interrupts!

#from collections import defaultdict
import os.path
import re
import sys
sys.path.append('/srv/radio/engine')
import skaianet

# regexps for valid values
# remember the settings values are always strings
# use r'^.*$' if they can be empty
#  more business-logic-y rules go later
SETTINGS_RULES = {
    "notifytext": r"^.*$",
    "notifytype": r"^[0-4]$",
    "requestlimit": r"^[1-9]$",
    "stationname": r"^[^\n<&]+$",
    "artworkurl":  r"^(https?:)?//radio\.skaia\.net/img/.*",
}
CONFIG_RULES = {
    "engine.jingle_interval": r"^(0|[1-9][0-9]+)$",
    "icecast.status_url": r"^http.*/status-json.xsl$",
}


def check_settings_in_config():
    " do the thing for config.ini, bark at strangers "
    # config is for backstage stuff
    # easier to shove this into a new struct
    success = True
    flatconfig = {}
    for i in skaianet.config.sections():
        for j, k in skaianet.config.items(i):
            flatconfig[f"{i}.{j}"] = k
    if flatconfig.get("db.mysql.dbname") and flatconfig.get("db.sqlite3.dbfile"):
        print(f"EROR config \"db.mysql.dbname\" and \"db.sqlite3.dbfile\" are both non-empty; use one xor the other")
        success = False

    for i, j in flatconfig.items():
        if i in CONFIG_RULES and not re.match(CONFIG_RULES[i], j):
            print(
                f"EROR config \"{i}\" value \"{j}\" does not match {CONFIG_RULES[i]}")
            success = False
        if 'path' in i and not os.path.isdir(j):
            f"EROR config \"{i}\" value \"{j}\" points to missing directory"
            success = False
        if i == "jingles.jingle_interval":
            j = int(j)
            if j == 0:
                pass
            elif j < 900:
                print(
                    f"WARN setting \"{i}\" value \"{j}\" is too small (< 15m)")
                success = False
            elif j < 86400:
                print(
                    f"WARN setting \"{i}\" value \"{j}\" is too large (> 1d)")
                success = False
    return success


def check_settings_in_db():
    " do the thing for settings table in db, bark at strangers "
    # settings table is for webUI stuff
    success = True
    for i in sorted(SETTINGS_RULES.keys()):
        j = skaianet.getsetting(i)
        if not re.match(SETTINGS_RULES[i], j):
            print(
                f"EROR setting \"{i}\" value \"{j}\" does not match {SETTINGS_RULES[i]}")
            success = False
    return success


def main():
    " Deploy cruxtruder "
    skaianet.initdb()
    if check_settings_in_db():
        print("OKAY settings passed")
    if check_settings_in_config():
        print("OKAY config.ini passed")


main()
