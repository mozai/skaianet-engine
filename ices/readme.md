Ices
====
Legacy code for using the shoutcast ices v0.4 (aka ices0)
to feed music to icecast.

Ices versions >0.x refused to process anything other than ogg vorbis
files, and oggvorbis is not universal (not supported by IE, IE Edge,
Safari for iOS, nor Opera Mini)

Ices versions 0.x depended upon Python 2.x, which is dead years ago.

Please use ezstream instead.

ices.conf.dist is because ices.conf must have a password in it.
