#!/usr/bin/python3
# something to automate changing the notifytext
import sys
sys.path.append('/srv/radio/engine')
import skaianet
import random

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
  'CC: Wonderful TUN--ES 38D'
]

def cleanse(i):
    return i.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

MESSAGE = cleanse(random.choice(MESSAGES))

if sys.stdin.isatty():
    skaianet.config.debug = True
skaianet.initdb()
skaianet.setsetting('notifytext',MESSAGE)
skaianet.closedb()

