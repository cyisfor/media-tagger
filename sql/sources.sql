CREATE OR REPLACE FUNCTION addsource(_media INTEGER, _source INTEGER) RETURNS void AS $$
BEGIN
	update media set sources = array(select unnest(sources) UNION select _source) WHERE id = _media;
END
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION findurisource(_uri text) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
_id int;
BEGIN
    LOOP
        -- first try to find it
        SELECT id INTO _id FROM urisources WHERE uri = _uri;
        IF found THEN
            return _id;
        END IF;
        BEGIN
            INSERT INTO sources DEFAULT VALUES RETURNING id INTO _id;
            INSERT INTO urisources (id,uri) VALUES (_id,_uri);
        EXCEPTION WHEN unique_violation THEN
            -- Do nothing we can just find it now.
        END;
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION addsource(_media INTEGER, _source text) RETURNS void AS $$
DECLARE
_sourceid INTEGER;
BEGIN
	update media set sources = array(select unnest(sources) UNION select findurisource(_source)) WHERE id = _media;
END
$$ LANGUAGE 'plpgsql';
