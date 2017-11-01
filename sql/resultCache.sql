CREATE SCHEMA IF NOT EXISTS resultCache;

CREATE TABLE resultCache.queries(
        id SERIAL PRIMARY KEY,
        digest TEXT UNIQUE,
				touched timestamptz DEFAULT clock_timestamp(),
        created timestamptz DEFAULT clock_timestamp());

CREATE OR REPLACE FUNCTION resultCache.updateQuery(_digest text) RETURNS void AS
$$
BEGIN
    LOOP
        UPDATE resultCache.queries SET touched = clock_timestamp() WHERE digest = _digest;
        IF found THEN
            RETURN;
        END IF;
        BEGIN
            INSERT INTO resultCache.queries (digest) VALUES (_digest);
        EXCEPTION
            WHEN unique_violation THEN
                -- do nothing
        END;
    END LOOP;
END;
$$ language 'plpgsql';

DROP FUNCTION resultCache.expireQueries();
CREATE OR REPLACE FUNCTION resultCache.expireQueries(_lower_bound int default 1000)
RETURNS int AS
$$
DECLARE
_id integer;
_count integer default 0;
_digest text;
BEGIN
	-- always leave the latest _lower_bound unexpired
    FOR _id,_digest IN SELECT id, digest FROM
				(SELECT id,digest,touched FROM resultCache.queries
													 ORDER BY touched ASC OFFSET _lower_bound) AS Q
				-- but still expire older queries first
				ORDER BY touched DESC LIMIT 1000

		LOOP
        BEGIN
            EXECUTE 'DROP TABLE resultCache."q' || _digest || '"';
            DELETE FROM resultcache.queries WHERE id = _id;
            _count := _count + 1;
        EXCEPTION
            WHEN undefined_table THEN
                -- do nothing
        END;
    END LOOP;
    RETURN _count;
END;
$$ language 'plpgsql';

-- we only want to drop queries depending on these particular tags
-- any of the tags added, or removed
-- even for new images, all the (positive) queries for added tags are invalidated
-- each query depends on a tag if

-- a search for "red, blue" would be invalidated if a picture were tagged with red,
-- or the tag were removed. Except if the blue tag were removed from a picture not also
-- tagged with red, then it's stay. Or if a red tag was added to a picture without a blue
-- tag, the query would remain valid.

-- a search for "red, -blue, -green" would not change if you tagged something with green.
-- provided it were tagged with blue, or not tagged with red.

-- a medium's tags have to match the tag query before alteration, for that query to expire

-- so... add an image, for each cached query, test that query against the image's tags
-- before remove an image, also do so
-- when re-tag an image, both the tags before and after have to be checked for matches.

-- query "red, blue" would not match "blue, green" but would match if you added "red" to that.
-- query "red, blue" would match "red, blue, green" but would not match if you removed "blue"
-- query "red, -blue" would not match "red, blue" but would match if you removed "blue"
-- query "red, -blue" would match "red" but would match if you added "blue"
-- add blue tag -> invalidates -blue BEFORE
-- remove blue tag -> invalidates -blue AFTER
-- add red tag -> invalidates red AFTER
-- remove red tag -> invalidates red BEFORE


-- so... can't do that on a trigger, since the query could have any number of tags
-- so just delete them all.

CREATE FUNCTION resultCache.expireQueriesTrigger();
 RETURNS trigger AS
$$
BEGIN
    PERFORM resultCache.expireQueries();
    RETURN OLD;
END;
$$ language 'plpgsql';

CREATE TRIGGER expireTrigger AFTER INSERT OR UPDATE OR DELETE ON things
    EXECUTE PROCEDURE resultCache.expireQueriesTrigger();
RETURNS int AS
$$
DECLARE
_id integer;
_count integer default 0;
_digest text;
BEGIN
	
