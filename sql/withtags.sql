complextagalter {
ALTER TABLE tags ADD COLUMN complexity int DEFAULT 0 NOT NULL
}
complextagindex {
CREATE INDEX bycomplex ON tags(complexity)
}
wanted {
wanted(tags) AS
(SELECT array(SELECT implications(unnest)) FROM unnest(%(tags)s::int[])) 
}
unwanted {
unwanted(id) AS (
        SELECT tags.id
            FROM tags INNER JOIN things ON tags.id = things.id 
            WHERE things.neighbors && %%(negatags)s::int[] 
            %(notWanted)s
        UNION
        SELECT id
            FROM unnest(%%(negatags)s::int[]) AS id)
}

notWanted {
AND NOT things.id = ANY(%(tags)s::int[])
}

positiveClause {
media INNER JOIN things ON things.id = media.id
}

positiveWhere {
    WHERE (SELECT EVERY(neighbors && wanted.tags) from wanted)
}

negativeClause {
    NOT neighbors && array(select id from unwanted %(anyWanted)s)
}		
anyWanted {
    where id NOT IN (select unnest(tags) from wanted)
}

ordering {
    ORDER BY media.added DESC
    OFFSET %(offset)s LIMIT %(limit)s
}

main {
SELECT
media.id,media.name,media.type,
    array(SELECT tags.name FROM tags INNER JOIN (SELECT unnest(neighbors)) AS neigh ON neigh.unnest = tags.id)
FROM
        %(positiveClause)s
        %(negativeClause)s
        %(notComic)s
    %(ordering)s
}

relatedNoTags {
    (NOT tags.id = ANY(%%(tags)s::int[])) AND
}

notComic {
  things.id NOT IN (select medium FROM comicPage)
}

related {
SELECT derp.id,derp.name FROM (SELECT tags.id,first(tags.name) as name FROM tags INNER JOIN things ON tags.id = ANY(things.neighbors) WHERE %(relatedNoTags)s things.id = ANY(
    SELECT things.id
FROM
        %(positiveClause)s
        %(negativeClause)s
        %(notComic)s
    %(ordering)s) 
    GROUP BY tags.id
    LIMIT %%(taglimit)s::int) AS derp ORDER BY derp.name
}
