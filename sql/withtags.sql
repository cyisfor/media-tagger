wanted 
wanted(tags) AS (SELECT array(
        SELECT tags.id 
            FROM tags INNER JOIN things ON tags.id = things.id WHERE things.neighbors @> ARRAY[unnest.unnest]
        ) || unnest.unnest AS tags
    FROM unnest(%(tags)s::bigint[]) AS unnest);
unwanted
unwanted(id) AS (
        SELECT tags.id
            FROM tags INNER JOIN things ON tags.id = things.id 
            WHERE things.neighbors && %%(negatags)s::bigint[] 
            %(notWanted)s
        UNION
        SELECT id
            FROM unnest(%%(negatags)s::bigint[]) AS id);
notWanted
AND NOT things.id = ANY(%(tags)s::bigint[]);
positiveClause
media INNER JOIN things ON things.id = media.id;
positiveWhere
    WHERE (SELECT every(neighbors && wanted.tags) FROM wanted);
negativeClause
NOT neighbors && array(select id from unwanted %(anyWanted)s);
anyWanted
where id != ANY(array(SELECT unnest(wanted.tags) FROM wanted)); 
ordering
    ORDER BY media.added DESC NULLS LAST 
    OFFSET %(offset)s LIMIT %(limit)s;
main
SELECT media.id,media.name,media.type,
    array(SELECT tags.name FROM tags WHERE tags.id = ANY(things.neighbors))
FROM
        %(positiveClause)s
        %(negativeClause)s
    %(ordering)s;
relatedNoTags
(NOT tags.id = ANY(%%(tags)s::bigint[])) AND;
related
SELECT tags.name FROM tags WHERE %(relatedNoTags)s tags.id = ANY(
    SELECT unnest(things.neighbors)
FROM
        %(positiveClause)s
        %(negativeClause)s
    %(ordering)s) LIMIT %%(taglimit)s::int;
connect
WITH nothing AS (
    UPDATE things SET neighbors = array(SELECT DISTINCT unnest(neighbors || $2::bigint)) WHERE id = $1)
UPDATE things SET neighbors = array(SELECT DISTINCT unnest(neighbors || $1::bigint)) WHERE id = $2;
