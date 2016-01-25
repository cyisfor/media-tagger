WITH media_tags AS (SELECT id AS medium,unnest AS tag FROM (SELECT things.id,unnest(neighbors) from things inner join media on media.id = things.id) AS derp WHERE unnest IN (select id FROM tags) LIMIT 50)
	 SELECT media_tags.medium, media_tags.tag, tags.name, media.name,
	 hash,created,added,size,type,md5,thumbnailed,sources,modified,phashfail,phash
	 FROM media_tags INNER JOIN tags ON tags.id = media_tags.tag
	 INNER JOIN media ON media.id = media_tags.medium
