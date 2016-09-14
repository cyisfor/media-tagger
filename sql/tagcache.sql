CREATE SCHEMA IF NOT EXISTS tagcache;
CREATE TABLE tagcache.queries (
	id SERIAL PRIMARY KEY,
	tags bigint[] UNIQUE,
	created timestamptz UNIQUE DEFAULT clock_timestamp());
	
CREATE OR REPLACE FUNCTION tagcache.expire(_changed_tags bigint[])
RETURNS int AS $$
DECLARE
_tags bigint[];
_id int;
BEGIN
	for _id,_tags in SELECT id,tags FROM tagcache.queries
			WHERE tags && _changed_tags
			ORDER BY created DESC LIMIT 1000
	LOOP BEGIN
		DELETE FROM tagcache.queries WHERE id = _id;
		EXECUTE 'DROP TABLE tagcache.q' | array_to_string(_tags,'_');
		_count := _count + 1;
	EXCEPTION
		WHEN undefined_table THEN
				 -- do nothing
		END;
	END LOOP;
	RETURN _count;
END;
$$ language 'plpgqsql';

CREATE OR REPLACE FUNCTION tagcache.query(_tags bigint[])
RETURNS text AS
$$
DECLARE
_name text;
BEGIN
_name := 'tagcache.q' || array_to_string(_tags,',');
UPDATE tagcache.queries SET created = clock_timestamp() WHERE tags = _tags;
	IF NOT found THEN
		BEGIN
		  EXECUTE 'CREATE TABLE ' || _name || ' AS SELECT unnest(neighbors) FROM things WHERE id = ANY($1)', _tags;
			INSERT INTO tagcache.queries (tags) VALUES (_tags);
		EXCEPTION
			WHEN unique_violation THEN
				-- do nothing
			END;
	END;
	RETURN _name;
END;
$$ language 'plpgsql';
