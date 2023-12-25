#!/usr/bin/env python3
" something to automate changing the notifytext "
import random
import sys
sys.path.append('/srv/radio/engine')
import skaianet

# remember to use HTML entities like &lt; and &amp;
MESSAGES = [
    'AA: s0unds f0r y0ur enj0yment 0u0',
    'AT: mUSIC WE HOPE YOU uHH ENJOY }:)',
    'TA: tune2 two bee grooviing',
    'CG: LISTEN WITH YOUR SKULLHOLES O:B',
    'AC: :3 << *plays mewsic for you*',
    'GA: Please Enjoy Responsibly',
    'GC: MUS1C W1TH GOOD T4ST3 >;]',
    'AG: you know my songs are the 8est :::;)',
    'CT: D --> e%ellent music',
    'TC: gRoOvY MuSiC :o)',
    'CA: music for evverybody',
    'CC: Wonderful TUN--ES 38D',

    'EB: Oh boy! More great tunes!',
    'TT: Music that is not at all suspicious',
    'TG: okay these tracks arent terrible',
    'GG: Yaaaaay more music! :D'

]


def cleanse(i):
    " clean up the string before sending it "
    return i.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


if sys.stdin.isatty():
    skaianet.config.debug = True
skaianet.initdb()
random.shuffle(MESSAGES)
oldmessage = skaianet.getsetting('notifytext')
newmessage = cleanse(MESSAGES[0])
if oldmessage == newmessage:
    newmessage = cleanse(MESSAGES[-1])
skaianet.setsetting('notifytext', newmessage)
skaianet.closedb()
