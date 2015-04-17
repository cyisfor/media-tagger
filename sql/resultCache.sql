CREATE SCHEMA IF NOT EXISTS resultCache;

CREATE TABLE resultCache.queries(
        id SERIAL PRIMARY KEY,
        digest TEXT UNIQUE,
        created timestamptz DEFAULT clock_timestamp());

CREATE OR REPLACE FUNCTION resultCache.updateQuery(_digest text) RETURNS void AS
$$
BEGIN
    LOOP
        UPDATE resultCache.queries SET created = clock_timestamp() WHERE digest = _digest;
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

CREATE OR REPLACE FUNCTION resultCache.expireQueries() RETURNS int AS
$$
DECLARE
_id integer;
_count integer default 0;
_digest text;
BEGIN
    FOR _id,_digest IN SELECT id,digest FROM resultCache.queries ORDER BY CREATED DESC LIMIT 1000 LOOP
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
CREATE OR REPLACE FUNCTION resultCache.expireQueriesTrigger() RETURNS trigger AS
$$
BEGIN
    PERFORM resultCache.expireQueries();
    RETURN OLD;
END;
$$ language 'plpgsql';

CREATE TRIGGER expireTrigger AFTER INSERT OR UPDATE OR DELETE ON things
    EXECUTE PROCEDURE resultCache.expireQueriesTrigger();
