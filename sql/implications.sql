--DROP FUNCTION implications(_tag INTEGER, _returned int, _depth int);

DROP FUNCTION unsafeImplications(_tag INTEGER	);
CREATE OR REPLACE FUNCTION unsafeImplications(_tag INTEGER) RETURNS void AS $$
DECLARE
_returned int default 1;
_count int;
_depth int default 0;
_other int;
BEGIN
		CREATE TEMPORARY TABLE IF NOT EXISTS impresult (id SERIAL PRIMARY KEY, tag INTEGER);
		DELETE FROM impresult;
		INSERT INTO impresult (tag) VALUES (_tag);
		LOOP
			WITH ins AS (INSERT INTO impresult (tag)
			  select tags.id FROM things INNER JOIN tags ON tags.id = things.id
			  WHERE
				complexity < (SELECT MAX(complexity) FROM impresult)
				AND
				neighbors && array(SELECT tag FROM impresult)
				EXCEPT SELECT tag FROM impresult
				LIMIT 100 - _returned
				RETURNING 1)
				SELECT COUNT(*) FROM ins INTO _count;
			RAISE NOTICE 'found tag %',_count;
			_returned := _returned + _count;
			IF _returned = 100 THEN return; END IF;
			_depth = _depth + 1;
			IF _depth = 2 THEN return; END IF;
		END LOOP;
END
$$ language 'plpgsql';
-- note: implications		caches implications for a given tag... THIS MAY BE INACCURATE but will be fast
drop function					 implications(_tag INTEGER);
CREATE OR REPLACE FUNCTION implications(_tag INTEGER) RETURNS SETOF INTEGER AS $$
DECLARE
_dest text;
BEGIN
	_dest := 'implications' || _tag;
	BEGIN
		EXECUTE format('CREATE TEMPORARY TABLE %I (tag INTEGER)',_dest);
		PERFORM unsafeImplications(_tag);
		EXECUTE format('INSERT INTO %I SELECT DISTINCT tag FROM impresult',_dest);
		--DROP TABLE impresult;
	EXCEPTION
		WHEN duplicate_table THEN
			 RAISE NOTICE 'yay already have';
	END;
	RETURN QUERY EXECUTE format('SELECT tag FROM %I',_dest);
END
$$
LANGUAGE 'plpgsql'
