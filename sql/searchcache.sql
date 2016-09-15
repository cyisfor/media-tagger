CREATE SCHEMA IF NOT EXISTS searchcache;

CREATE TABLE IF NOT EXISTS searchcache.queries (
id SERIAL PRIMARY KEY,
name TEXT NOT NULL UNIQUE,
count int NOT NULL);

CREATE TABLE IF NOT EXISTS searchcache.tree (
id SERIAL PRIMARY KEY,
child INTEGER NOT NULL REFERENCES searchcache.queries(id) ON DELETE CASCADE ON UPDATE CASCADE,
parent INTEGER NOT NULL REFERENCES searchcache.queries(id) ON DELETE CASCADE ON UPDATE CASCADE,
UNIQUE(child,parent));

create or replace function searchcache.lookup(_name TEXT)
RETURNS int
AS $$
DECLARE
_id int;
BEGIN
LOOP
	SELECT id INTO _id FROM searchcache.queries WHERE name = _name;
	IF NOT found THEN
		RAISE EXCEPTION 'need to insert proactively to keep an accurate count';
	END IF;
END LOOP;
END;
$$ language 'plpgsql';

create or replace function searchcache.reduce(_a int, _b int, _op TEXT)
RETURNS int
AS $$
DECLARE
_at TEXT;
_bt TEXT;
_name TEXT;
_result INTEGER;
BEGIN
  SELECt name INTO _at FROM searchcache.queries WHERE id = _a;
  if NOT FOUND THEN
	  RAISE EXCEPTION 'Should not be null! % %',_a,_b;
  END IF;
	SELECT name INTO _bt FROM searchcache.queries WHERE id = _b; 
  if NOT FOUND THEN
	  RAISE EXCEPTION 'B Should not be null! % %',_at,_b;
  END IF;
	_name = 's' || _a || '_' || _b || '_' || _op;
	RAISE NOTICE '% + % => %', _at, _bt, _name;
	IF EXISTS (SELECT 1 FROM searchcache.queries WHERE name = _name) THEN
		RETURN _name;
	END IF;
--	RAISE NOTICE '%','DERP CREATE TABLE searchcache.' || _name || ' AS SELECT id FROM searchcache.' || _at || ' ' || _op || ' ' || 'SELECT id FROM searchcache.' || _bt;
	EXECUTE 'CREATE TABLE searchcache.' || _name || ' AS SELECT id FROM searchcache.' || _at || ' ' || _op || ' ' || 'SELECT id FROM searchcache.' || _bt;
	GET DIAGNOSTICS _result = ROW_COUNT;
	INSERT INTO searchcache.queries (count,name) VALUES (_result,_name) RETURNING id INTO _result;
	INSERT INTO searchcache.tree (child,parent) VALUES (_a, _result);
	INSERT INTO searchcache.tree (child,parent) VALUES (_b, _result);
	-- when unique violation...?
	RETURN _result;
END;
$$ language 'plpgsql';

create or replace function searchcache.one_tag(_tag bigint)
RETURNS int
AS $$
DECLARE
_result int;
_name text;
BEGIN
	_name = 't' || _tag;
	SELECT id INTO _result FROM searchcache.queries WHERE name = _name;
	IF found THEN
		RETURN _result;
	END IF;
	EXECUTE 'CREATE TABLE searchcache.' || _name || ' AS SELECT unnest(neighbors) AS id FROM things WHERE id = $1' USING _tag;
	GET DIAGNOSTICS _result = ROW_COUNT;
	INSERT INTO searchcache.queries (count,name) VALUES (_result,_name) RETURNING id INTO _result;
	-- just leave this empty, never need to cascade into the base tags.
	--	INSERT INTO searchcache.tree (child,parent) VALUES (NULL,searchcache.lookup(_result));
	RETURN _result;
END;
$$ language 'plpgsql';

create or replace function searchcache.reduce_implications(_result int, _tag bigint, _implications bigint[],  _op text)
RETURNS int
AS $$
DECLARE
_subresult int;
BEGIN
		FOR _tag IN SELECT implications FROM implications(_tag) ORDER BY implications LOOP
			IF _subresult IS NULL THEN
				_subresult = searchcache.one_tag(_tag);
				IF _result IS NULL THEN
					 _result = _subresult;
				END IF;
			ELSE
				_subresult = searchcache.reduce(_result, searchcache.one_tag(_tag), 'UNION');
			END IF;
		END LOOP;
		IF _result IS NULL THEN
			 return _subresult;
		ELSE
			return searchcache.reduce(_result,_subresult,_op);
		END IF;
END;
$$ language 'plpgsql';

create or replace function searchcache.query(_posi bigint[], _nega bigint[])
RETURNS text
AS $$
DECLARE
_result int;
_name TEXT;
_negresult int;
_curimp bigint[];
_imp bigint[]; -- don't let any implications of positives end up in implications of negatives.
-- this is so +character -character:foo will eliminate character:foo, but not character:bar
_tag bigint;
BEGIN
	FOREACH _tag IN ARRAY _posi LOOP
		PERFORM unsafeImplications(_tag);
		-- no need to follow positive implications twice!
		DELETE from impresult WHERE tag = ANY(_imp);
	  _curimp = array(SELECT id FROM impresult);
		_result = searchcache.reduce_implications(_result, _tag, _curimp, 'INTERSECT');
		_imp = _imp || _curimp;
	END LOOP;
	_imp = array(SELECT DISTINCT unnest FROM unnest(_imp));
	FOREACH _tag IN ARRAY _nega LOOP
		-- don't let any implications of positives end up in implications of negatives.
		PERFORM unsafeImplications(_tag);
		DELETE from impresult WHERE tag = ANY(_imp);
		_negresult = searchcache.reduce_implications(_negresult, _tag, array(SELECT DISTINCT id FROM impresult), 'UNION');
		_imp = _imp || _curimp;
	END LOOP;
	IF _curimp IS NOT NULL THEN
		 DROP TABLE impresult; -- I am such a hack
	END IF;
	IF _negresult IS NOT NULL THEN
		 _result = searchcache.reduce(_result,_negresult,'EXCEPT');
	END IF;
	SELECT name INTO _name FROM searchcache.queries WHERE id = _result;
	return _name;
END;
$$
language 'plpgsql';


create or replace function searchcache.really_expire(_query int)
RETURNS void
AS $$
DECLARE
_name text;
BEGIN
	--	 DELETE FROM searchcache.tree WHERE child = _query;
	raise NOTICE 'expire (%)',_query;

	 FOR _name IN SELECT name FROM searchcache.queries WHERE id = _query LOOP
	 	 EXECUTE 'DROP TABLE searchcache.' || _name || ' CASCADE';
	 	 DELETE FROM searchcache.queries WHERE id = _query;
	 END LOOP;
END
$$ LANGUAGE 'plpgsql';

create or replace function searchcache.follow_expire(_query int)
RETURNS int
AS $$
DECLARE
_count int DEFAULT 1;
_sub int;
BEGIN
	FOR _sub IN SELECT DISTINCT parent FROM searchcache.tree WHERE child = _query LOOP
			raise NOTICE 'uhh % -> %',_query,_sub;
	 		_count = _count + searchcache.follow_expire(_sub);
	 END LOOP;
	 PERFORM searchcache.really_expire(_query);
	 RETURN _count;
END;
$$ language 'plpgsql';

create or replace function searchcache.expire(_newtags bigint[])
RETURNS int
AS $$
DECLARE
_count int DEFAULT 0;
_base int;
_basequeries int[] DEFAULT array(SELECT id FROM searchcache.queries INNER JOIN (select implications(unnest) AS tag from unnest(_newtags) UNION SELECT unnest(_newtags) AS tag) AS imps ON queries.name = 't' || imps.tag);
BEGIN
  raise NOTICE 'clearing tags %',_basequeries;
	FOREACH _base IN ARRAY _basequeries LOOP
		_count = _count + searchcache.follow_expire(_base);
		PERFORM searchcache.really_expire(_base);
	END LOOP;
	RETURN _count;
END;
$$ language 'plpgsql';
