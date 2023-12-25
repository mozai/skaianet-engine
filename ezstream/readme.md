EZstream for radio.skaia.net
============================
Ices versions above 0.x refused to process or send mp3 files.
Ices version 0.4 (aka ices0) depended on python2.7 which died years ago.
EZstream v1.0.2 replaces ices v0.4

ref. https://icecast.org/ezstream/

* Con: Either uses a static list of files, or launches a program at the end of each song.
* Pro: if I want to change the get-next-song method I don't have to kill the daemon.
* Pro: I can tell is what to use for cooking data, like lame or ffmpeg
* Con: yet another process open to cook the audio stream on-the-fly
* Pro: can handle audio/opus and audio/flac
* Pro: no python 2.x dependency

Because config.xml must hold a password, can't commit it to the git repo,
so you'll need to `cp config.xml.example config.xml` and edit the
password in by hand.

