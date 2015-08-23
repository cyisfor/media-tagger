SELECT id,name,hash,created,added,size,type,md5,thumbnailed,sources,modified,phashfail,phash from media;
SELECT id,name FROM tags;
SELECT id,unnest FROM (SELECT things.id,unnest(neighbors) from things inner join media on media.id = things.id) AS derp WHERE unnest IN (select id FROM tags);
