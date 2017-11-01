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

CREATE OR REPLACE FUNCTION resultCache.expireQuery() RETURNS int AS
$$
BEGIN
    DROP SCHEMA resultCache;
		CREATE SCHEMA resultCache;
END;

DROP TRIGGER expireTrigger ON things;

