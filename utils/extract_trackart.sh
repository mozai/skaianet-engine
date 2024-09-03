#!/bin/bash
# for each *mp3 file in this directory, pull out track art
# TODO: ogg vorbis

declare -a TARGETS
for f in "$@"; do
	if [[ $f =~ .mp3 ]]; then
		TARGETS+=("$f")
	else
		echo "unrecognized file $f"
	fi
done
if [[ -z "${TARGETS[*]}" ]]; then
	echo >&2 "Usage: $0 file1.mp3 [file2.mp3 file3.mp3 ...]"
	echo >&2 "  attempts to pull the track art out and write to file1.jpg file2.jpg ..."
	exit 1
fi

for f in "${TARGETS[@]}"; do
	echo "Checking $f"
	g=${f%.mp3}
	if [[ -e "$g.jpg" ]]; then
		echo "$g.jpg already exists"
		continue
	elif [[ -e "$g.png" ]]; then
		echo "$g.png already exists"
		continue
	fi
	# dump all the images to local dir, clobbering what might be here oups
	eyeD3 "$f" --write-images .
	# then move one of them in the chair for track art
	if [[ -e FRONT_COVER.png ]]; then
		mv -v FRONT_COVER.png "$g.png"
	elif [[ -e FRONT_COVER.jpg ]]; then
		mv -v FRONT_COVER.jpg "$g.jpg"
	elif [[ -e OTHER.jpg ]]; then
		mv -v OTHER.jpg "$g.jpg"
	elif [[ -e OTHER.png ]]; then
		mv -v OTHER.png "$g.png"
	else
		echo "didn't find image FRONT_COVER nor OTHER in $f"
	fi
	rm -f FRONT_COVER.png FRONT_COVER.jpg OTHER.jpg OTHER.png
done

