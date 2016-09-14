
CREATE OR REPLACE FUNCTION tagcache.query(_tags bigint[])
RETURNS text AS
$$
DECLARE
_name text;
BEGIN
	_name := 'tagcache.q' || array_to_string(_tags,',');
	UPDATE tagcache.queries SET created = clock_timestamp() WHERE tags = _tags;
	IF found THEN
		RETURN _name;
	END;
	BEGIN
		EXECUTE 'CREATE TABLE ' || _name || ' AS SELECT unnest(neighbors) FROM things WHERE id = ANY($1)', _tags;
		INSERT INTO tagcache.queries (tags) VALUES (_tags);
	EXCEPTION
		WHEN unique_violation THEN
			-- do nothing
	END;
	RETURN _name;
END;
$$ language 'plpgsql';
