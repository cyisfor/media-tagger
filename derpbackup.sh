pg_dump -p 5433 pics > /extra/user/filedb/pics.sql
rsync -aPv --exclude-from ~/code/image/tagger/.gitignore ~/code/image/tagger/ /extra/user/filedb/code/
rsync -aPv --prune-empty-dirs --delete --exclude "thumb" --exclude "pendingThumb" --exclude "temp" --exclude "incoming" --exclude "pending" --exclude "resized" -u /extra/user/filedb/ user@192.168.1.2:~/filedb/
exec vacuumdb -f -z -a -p 5433
