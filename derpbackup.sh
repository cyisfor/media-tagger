#!/bin/sh

here=`dirname $0`
sh $here/dedup/doit.sh
pg_dump -p 5433 pics > ~/.local/filedb/pics.sql
rsync -aPv --exclude-from ~/code/image/tagger/.gitignore ~/code/image/tagger/ ~/.local/filedb/code/
rsync -aPv --prune-empty-dirs --delete --exclude "thumb" --exclude "pendingThumb" --exclude "temp" --exclude "incoming" --exclude "pending" --exclude "resized" -u ~/.local/filedb/ user@192.168.1.2:~/filedb/
#exec vacuumdb -z -a -p 5433
