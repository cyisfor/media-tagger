main
SELECT media.id,media.name,media.type,
    array(SELECT tags.name FROM tags WHERE tags.id = ANY(things.neighbors))
FROM media INNER JOIN 
    listMedia(%(tags)s::bigint[],%(negatags)s::bigint[],%(offset)s,%(limit)s) AS foo 
    ON foo = media.id 
    INNER JOIN things ON media.id = things.id
    ORDER BY media.added DESC NULLS LAST;
relatedNoTags
(NOT tags.id = ANY(%(tags)s::bigint[])) AND;
related
SELECT tags.name FROM tags INNER JOIN things ON tags.id = ANY(things.neighbors) WHERE %(relatedNoTags)s things.id = ANY(
    SELECT foo FROM listMedia(%%(tags)s::bigint[],%%(negatags)s::bigint[],%%(offset)s,%%(limit)s) AS foo) LIMIT %%(taglimit)s;
