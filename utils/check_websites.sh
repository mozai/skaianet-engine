#!/bin/bash
# I write down the URLs where music was found, but
#   linkrot is a thing, ESPECially with whatpumpkin
#   moving the albums around and erasing cover art >_<

DBFILE="/home/radio/db/skaianet.db"

get_song_urls(){
  sqlite3 "$DBFILE" 'select website,filepath from songs where website != "" order by 1;'
}

declare -A seen
while read -r line; do
	IFS='|' read -r website filepath <<<"$line"
	website=${website/http:/https:}
	if [[ -z "$website" ]] || [[ ${website,,} == "none" ]]; then
		continue;
	fi
	if [[ -n "${seen[$website]}" ]]; then
		httpcode=${seen[$website]}
	else
		httpcode=$(curl --silent --output /dev/null --write-out "%{http_code}" "$website" 2>/dev/null)
		seen[$website]=$httpcode
	fi
	if [[ $httpcode == "200" ]]; then
		: pass
	else
		echo "WARN HTTP ${httpcode} for file \"$filepath\" website \"$website\""
	fi
	seen[$website]=$httpcode
done < <(get_song_urls)

