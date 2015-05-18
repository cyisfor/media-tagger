complextagalter {
ALTER TABLE tags ADD COLUMN complexity int DEFAULT 0 NOT NULL
}
complextagindex {
CREATE INDEX bycomplex ON tags(complexity)
}
implications {
CREATE FUNCTION implications(_tags bigint[]) RETURNS SETOF bigint AS $$
BEGIN    
    FOREACH _tag IN ARRAY tags
    LOOP
     _complexity := SELECT complexity FROM tags WHERE id = _tag
     IF FOUND THEN
        RETURN NEXT _tag
        RETURN QUERY SELECT tag FROM implications(
               array(SELECT unnest(neighbors) FROM things
                            INNER JOIN tags ON tags.id = _neighbor
                            WHERE things.id = _tag
                            AND tags.complexity >  _complexity))
     END IF;
   END LOOP;
END
$$
LANGUAGE 'plpgsql'
}
wanted {
wanted(tags) AS (SELECT array(implications(%(tags)s::bigint[])))
}
unwanted {
unwanted(id) AS (
        SELECT tags.id
            FROM tags INNER JOIN things ON tags.id = things.id 
            WHERE things.neighbors && %%(negatags)s::bigint[] 
            %(notWanted)s
        UNION
        SELECT id
            FROM unnest(%%(negatags)s::bigint[]) AS id);
}

notWanted {
AND NOT things.id = ANY(%(tags)s::bigint[]);
}

positiveClause {
media INNER JOIN things ON things.id = media.id;
}

positiveWhere {
    WHERE (SELECT every(neighbors && wanted.tags) FROM wanted);
}

negativeClause {
    NOT neighbors && array(select id from unwanted %(anyWanted)s);
}

anyWanted {
    where id != ANY(array(SELECT unnest(wanted.tags) FROM wanted));
}

ordering {
    ORDER BY media.added DESC
    OFFSET %(offset)s LIMIT %(limit)s;
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
    LIMIT %%(taglimit)s::int) AS derp ORDER BY derp.name;
}
