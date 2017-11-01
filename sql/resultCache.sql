CREATE SCHEMA IF NOT EXISTS resultCache;

CREATE TABLE resultCache.queries(
        id SERIAL PRIMARY KEY,
        digest TEXT NOT NULL UNIQUE,
				used INTEGER NOT NULL DEFAULT 0,
				touched timestamptz NOT NULL DEFAULT clock_timestamp(),
        created timestamptz NOT NULL DEFAULT clock_timestamp());


-- of course, we can't expire more than 10,000 queries, so
-- just mark them as doomed I guess

create table if not exists resultcache.doomed (
			 id integer primary key,
			 digest text NOT NULL UNIQUE);

-- if a query is in doomed, the actual table needs to be purged, before
-- we create a new one, with new results!
CREATE OR REPLACE FUNCTION resultCache.cleanQuery(_digest text)
RETURNS bool
language 'plpgsql';
AS
$$
BEGIN
	DELETE FROM resultCache.doomed WHERE digest = _digest;
	IF found THEN
		-- maybe we should do this anyway...?
		EXECUTE 'DROP MATERIALIZED VIEW resultCache."q' || _digest || '"';
		RETURN TRUE;
	END IF
	RETURN FALSE;
END
$$

-- be sure to call cleanQuery before you create the table, then updateQuery after you do!
-- we successfully created the query, now mark it as active
CREATE OR REPLACE FUNCTION resultCache.updateQuery(_digest text) RETURNS void AS
$$
BEGIN
    LOOP
				-- this might be good for debugging, but shouldn't be necessary with good code
				-- PERFORM FROM resultCache.doomed WHERE digest = _digest;
				-- IF found THEN
				-- 	 -- uh... this is bad.
				-- 	 RAISE EXCEPTION 'please cleanQuery %i before updateQuerying it', _digest;
				-- END IF;
				INSERT INTO resultCache.queries (digest) VALUES (_digest)
				ON CONFLICT DO UPDATE SET touched = clock_timestamp();
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
	WITH results AS (
    INSERT INTO resultCache.doomed SELECT id, digest FROM
				(SELECT id,digest,touched FROM resultCache.queries
													 ORDER BY touched ASC OFFSET _lower_bound) AS Q
				-- but still expire older queries first
				ORDER BY touched DESC LIMIT 1000
		ON CONFLICT DO NOTHING
		RETURNING 1
		)
		SELECT count(*) INTO _count FROM results;
	RETURN _count;
	-- still need to purge these though!
END;
$$ language 'plpgsql';


-- this actually deletes the queries.
-- you must run it in a loop, since no postgresql function can commit a transaction.
-- until it returns less than 1000, or returns 0
CREATE OR REPLACE FUNCTION resultCache.purgeQueries() RETURNS int AS
$$
DECLARE
_id integer;
_count integer default 0;
_digest text;
BEGIN
	-- always leave the latest _lower_bound unexpired
    FOR _id,_digest IN SELECT id,digest from resultCache.doomed LIMIT 1000
		LOOP
        BEGIN
            EXECUTE 'DROP MATERIALIZED VIEW resultCache."q' || _digest || '"';
            DELETE FROM resultCache.doomed WHERE id = _id;
            _count := _count + 1;
        EXCEPTION
            WHEN undefined_table THEN
                -- do nothing
        END;
    END LOOP;
    RETURN _count;
END;
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION resultCache.refresh(_limit int default 100);
RETURNS int AS
$$
DECLARE
_id integer;
_count integer default 0;
_digest text;
BEGIN
		-- this should take next to forever...
    FOR _id,_digest IN SELECT id,digest from resultCache.refresh LIMIT _limit
		LOOP
        BEGIN
            EXECUTE 'REFRESH MATERIALIZED VIEW resultCache."q' || _digest || '"';
						_count := _count + 1;
        EXCEPTION
            WHEN undefined_table THEN
                -- do nothing
				END;
		END LOOP;
END;
$$ language 'plpgsql';

CREATE or replace FUNCTION resultCache.expireQueriesTrigger();
 RETURNS trigger AS
$$
BEGIN
		-- see below for why we can't do this selectively.
		insert into resultCache.refresh select id, digest from resultcache.queries;
		delete from resultcache.queries;
    RETURN OLD;
END;
$$ language 'plpgsql';

CREATE TRIGGER expireTrigger AFTER INSERT OR UPDATE OR DELETE ON things
    EXECUTE PROCEDURE resultCache.expireQueriesTrigger();


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
-- so, if only adding tags... (creating an image)
--   then any query with only positive tags would only have to be checked AFTER
--   any query with only negative tags would only have to be checked BEFORE

-- meh, too complicated
