# skaianet-engine

This is software for a library of music and publishing the music to an
icecast streaming media service.
It can accept requests from listeners and have seasonal preferences
for music selection.

**This part also out-of-date** Moved to html+vanillajavascript+api
instead of jquery+PHP .
~~This doesn't have a UI, this is the back-end.  Check out
[skaianet-web](https://github.com/skaianet-radio/skaianet-web) for the
user-facing stuff.~~


## TODO

* better Setup instructions
* re-add the station-identification jingles feature
* merge the webui parts into this because why would
  not use that with this?

## Requirements

* python with python module "mutagen"
* icecast, and ezstream
* (optional) mysqld and python module mysql.connector
* (optional) ffmpeg for music masaging

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
* using ezstream now.

 

## Disclaimer
This software was only ever made for one instance deployment, so we hereby
go above and beyond the GPL 3.0 license's limitation of liability and
warranty to warn you that this project may not be fit for whatever you
would like to use it for, and that it may just make whatever you run it
on immediately self destruct.  Use it at your own risk.


## Contributors
* [Mozai](https://github.com/mozai)
* [Kitty](https://github.com/KiTTYsh)

