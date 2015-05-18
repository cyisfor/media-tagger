complextagalter {
ALTER TABLE tags ADD COLUMN complexity int DEFAULT 0 NOT NULL
}
complextagindex {
CREATE INDEX bycomplex ON tags(complexity)
}
implications {
CREATE OR REPLACE FUNCTION implications(_tags bigint[]) RETURNS SETOF bigint AS $$
DECLARE
_complexity int;
_tag bigint;
_neighbor bigint;
BEGIN    
    FOREACH _tag IN ARRAY _tags
    LOOP
     SELECT complexity INTO _complexity FROM tags WHERE id = _tag;
     IF FOUND THEN
        RETURN NEXT _tag;
        RETURN QUERY SELECT implications FROM implications(
               array(SELECT unnest(neighbors) FROM things
                            INNER JOIN tags ON neighbors @> ARRAY[tags.id]
                            WHERE things.id = _tag
                            AND tags.complexity >  _complexity));
     END IF;
   END LOOP;
END
$$
LANGUAGE 'plpgsql'
}
wanted {
wanted(tag) AS (SELECT implications FROM implications(%(tags)s::bigint[]))
}
unwanted {
unwanted(id) AS (
        SELECT tags.id
            FROM tags INNER JOIN things ON tags.id = things.id 
            WHERE things.neighbors && %%(negatags)s::bigint[] 
            %(notWanted)s
        UNION
        SELECT id
            FROM unnest(%%(negatags)s::bigint[]) AS id)
}

notWanted {
AND NOT things.id = ANY(%(tags)s::bigint[])
}

positiveClause {
media INNER JOIN things ON things.id = media.id
}

positiveWhere {
    WHERE neighbors && array(select wanted.tag from wanted)
}

negativeClause {
    NOT neighbors && array(select id from unwanted %(anyWanted)s)
}

anyWanted {
    where id NOT IN (select tag from wanted)
}

ordering {
    ORDER BY media.added DESC
    OFFSET %(offset)s LIMIT %(limit)s
}

main {
SELECT media.id,media.name,media.type,
    array(SELECT tags.name FROM tags INNER JOIN (SELECT unnest(neighbors)) AS neigh ON neigh.unnest = tags.id)
FROM
        %(positiveClause)s
        %(negativeClause)s
    %(ordering)s
}

relatedNoTags {
    (NOT tags.id = ANY(%%(tags)s::bigint[])) AND
}

related {
SELECT derp.id,derp.name FROM (SELECT tags.id,first(tags.name) as name FROM tags INNER JOIN things ON tags.id = ANY(things.neighbors) WHERE %(relatedNoTags)s things.id = ANY(
    SELECT things.id
FROM
        %(positiveClause)s
        %(negativeClause)s
    %(ordering)s) 
    GROUP BY tags.id
    LIMIT %%(taglimit)s::int) AS derp ORDER BY derp.name
}
