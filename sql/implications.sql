DROP FUNCTION implications(_tag INTEGER, _returned int, _depth int);
CREATE OR REPLACE FUNCTION implications(_tag INTEGER, _returned int, _depth int) RETURNS int AS $$
DECLARE
_neighbor INTEGER;
_count int default 0;
BEGIN
    IF _depth > 2 THEN
       RETURN _count;
    END IF;
	IF _returned > 100 THEN
	   RETURN _count;
	END IF;


    _count := _count + 1;
	_count := sum(implications(
             other.id,
             _returned + _count,
             1 + _depth))
        FROM tags as curr inner join things on things.id = curr.id , tags as other WHERE
			 curr.id = _tag
			 AND other.id = ANY(things.neighbors)
			 AND curr.complexity < other.complexity;
	RETURN _count;
END
$$
LANGUAGE 'plpgsql';

DROP FUNCTION unsafeImplications(_tag INTEGER	);
CREATE OR REPLACE FUNCTION unsafeImplications(_tag INTEGER) RETURNS void AS $$
DECLARE
_returned int default 0;
_depth int default 0;
BEGIN
		CREATE TEMPORARY TABLE IF NOT EXISTS impresult (tag INTEGER);
		DELETE FROM impresult;
		INSERT INTO impresult (tag) VALUES (_tag);
		LOOP
			FOR _other IN select id FROM things INNER JOIN tags ON tags.id = things.id
			  WHERE neighbors && array(SELECT id FROM impresult)
				EXCEPT SELECT id FROM impresult LOOP
          RAISE NOTICE 'found tag % % %s',_other,(select name from tags where id = _other);
					INSERT INTO impresult (tag) VALUES (_other);
				IF _returned = 100 THEN return END IF
				_returned := _returned + 1
			END LOOP;
			IF _depth = 2 THEN return END IF
			_depth = _depth + 1;
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
		DROP TABLE impresult;
	EXCEPTION
		WHEN duplicate_table THEN
			 RAISE NOTICE 'yay already have';
	END;
	RETURN QUERY EXECUTE format('SELECT tag FROM %I',_dest);
END
$$
LANGUAGE 'plpgsql'
