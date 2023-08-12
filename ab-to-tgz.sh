#!/bin/bash

# Convert Android backup files (.ab) files to tgz files. Takes filename
# as argument, produces tgz file on stdout.

# From https://stackoverflow.com/a/46500482/740048
if [ ! -e "$1" ]; then
	echo "Specify ab file"
	exit 1
fi
printf "\x1f\x8b\x08\x00\x00\x00\x00\x00" ; tail -c +25 "$@"
