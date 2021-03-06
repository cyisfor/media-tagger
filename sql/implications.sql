DROP FUNCTION implications(_tag INTEGER, _returned int, _depth int);
CREATE OR REPLACE FUNCTION implications(_tag INTEGER, _returned int, _depth int) RETURNS int AS $$
DECLARE
_neighbor INTEGER;
_count int NOT NULL default 0;
BEGIN
    IF _depth > 2 THEN
       RETURN _returned;
    END IF;
	IF _returned > 100 THEN
	   RETURN _returned;
	END IF;
    INSERT INTO impresult (tag) VALUES (_tag);
	RAISE NOTICE 'found tag % % % %s',_returned,_depth,_tag,(select name from tags where id = _tag);
    _count := _count + 1;
	FOR _neighbor IN SELECT other.id FROM tags
	  inner join things on things.id = tags.id ,
		tags other
		WHERE tags.id = _tag AND other.id = ANY(things.neighbors) AND tags.complexity < other.complexity
		LIMIT 100 - (_returned + _count)
		LOOP
		_count := _count + COUNT(*) FROM implications(
		             _neighbor,
								 _returned + _count,
								 1 + _depth);
	END LOOP;
	RAISE NOTICE 'implications %',_count;
	RETURN _count;
END
$$
LANGUAGE 'plpgsql';

DROP FUNCTION unsafeImplications(_tag INTEGER);
CREATE OR REPLACE FUNCTION unsafeImplications(_tag INTEGER) RETURNS void AS $$
BEGIN
		CREATE TEMPORARY TABLE IF NOT EXISTS impresult (tag INTEGER);
		DELETE FROM impresult;
		PERFORM implications( _tag, 0, 0);
END;
$$ language 'plpgsql';
-- note: implications caches implications for a given tag... THIS MAY BE INACCURATE but will be fast
CREATE OR REPLACE FUNCTION implications(_tag INTEGER) RETURNS SETOF INTEGER AS $$
DECLARE
_dest text;
BEGIN
	_dest := 'implications' || _tag;
	BEGIN
		EXECUTE format('CREATE TEMPORARY TABLE %I (tag INTEGER)',_dest);
		PERFORM unsafeImplications(_tag);
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
