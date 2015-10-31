complextagalter {
ALTER TABLE tags ADD COLUMN complexity int DEFAULT 0 NOT NULL
}
complextagindex {
CREATE INDEX bycomplex ON tags(complexity)
}
implications {
CREATE OR REPLACE FUNCTION implications(_tag bigint, _returned int, _depth int) RETURNS int AS $$
DECLARE
_neighbor bigint;
_count int default 0;
BEGIN
    IF _depth > 2 THEN
       RETURN _count;
    END IF;
	IF _returned > 100 THEN
	   RETURN _count;
	END IF;
    INSERT INTO impresult (tag) VALUES (_tag);
	RAISE NOTICE 'found tag %s',(select name from tags where id = _tag);
    _count := _count + 1;
	_count := sum(implications(
             other.id,
             _returned + _count,
             1 + _depth))
        FROM tags inner join things on things.id = tags.id , tags other WHERE
			 tags.id = _tag
			 AND other.id = ANY(things.neighbors)
             AND tags.complexity < other.complexity;
	RETURN _count;
END
$$
LANGUAGE 'plpgsql'
}
implicationsderp {
CREATE OR REPLACE FUNCTION implications(_tag bigint) RETURNS SETOF bigint AS $$
DECLARE
_dest text;
BEGIN
	_dest := 'implications' || _tag;
	BEGIN
		EXECUTE format('CREATE TEMPORARY TABLE %I (tag BIGINT)',_dest);
		CREATE TEMPORARY TABLE IF NOT EXISTS impresult (tag BIGINT);
		DELETE FROM impresult;
		PERFORM implications( _tag, 0, 0);
		EXECUTE format('INSERT INTO %I SELECT DISTINCT tag FROM impresult',_dest);
		DROP TABLE impresult;
	EXCEPTION
		WHEN duplicate_table THEN
			 RAISE NOTICE 'yay already have';
	END;
	RETURN QUERY EXECUTE format('SELECT tag FROM %I',_dest);
END
$$
LANGUAGE 'plpgsql'
}
wanted {
wanted(tags) AS
(SELECT array(SELECT implications(unnest)) FROM unnest(%(tags)s::bigint[])) 
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
