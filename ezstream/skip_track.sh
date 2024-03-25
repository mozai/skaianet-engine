#!/bin/sh
# skip currently playing track
#   because I keep forgetting the kill signal

# TODO: tell ezstream to write to a pid file, use that instead of pkill

pkill -SIGUSR1 ezstream
