mkdir /dev/shm/convert
psql -p 5433 -U ion pics <pull.sql
psql -p 5433 -U ion derp <../schema.sql
psql -p 5433 -U ion derp <push.sql
echo yay
