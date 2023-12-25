# skaianet-engine

This is a set of python2 scripts designed for maintaining a library
of music and publishing the music to an icecast streaming media service.
It can accept requests from listeners, ~~and station-identification jingles
at intervals.~~

This doesn't have a UI, this is the back-end.  Check out
[skaianet-web](https://github.com/skaianet-radio/skaianet-web) for the
user-facing stuff.


## TODO

* finish updating to Python 3.x
* better Setup instructions
* move from mysql to sqlite3
* re-add the station-identification jingles feature


## Requirements

* python
* python module mutagen
* icecast, and ezstream
* mysqld and python module mysql.connector

In Ubuntu you should already have python, get the rest with: `apt-get
install python-mutagen python-mysql.connector icecast2 ezstream
mariadb-server`.


## Setup

**These instructions are out-of-date.**  Ices0 deprecated in 2018.

* ~~Install [ices
  0.4](http://downloads.us.xiph.org/releases/ices/ices-0.4.tar.gz).~~
* Copy config.py.dist to config.py and edit the file appropriately.
* ~~Copy ices.conf.dist to ices.conf and edit the file appropriately.~~
* Make a MySQL database and populate it with extra/schema.sql  (This
  should be done automatically further down the developmental road.)
* ~~Execute $ ices -c radio.conf~~

* Have a look at
  [skaianet-web](https://github.com/skaianet-radio/skaianet-web) if you're
  interested in using our web interface.


## Disclaimer
This software is still indevelopment, so we hereby go above and beyond
the GPL 3.0 license's limitation of liability and warranty to warn you
that this project may not be fit for whatever you would like to use
it for, and that it may just make whatever you run it on immediately
self destruct.  Use it at your own risk.


## Contributors
* Kitty (https://github.com/KiTTYsh)
* Mozai (https://github.com/mozai/)

