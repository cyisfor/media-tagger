CREATE SCHEMA IF NOT EXISTS searchcache;

CREATE TABLE IF NOT EXISTS searchcache.queries (
id SERIAL PRIMARY KEY,
name TEXT UNIQUE);

CREATE TABLE IF NOT EXISTS searchcache.tree (
id SERIAL PRIMARY KEY,
child INTEGER NOT NULL REFERENCES searchcache.queries(id) ON DELETE CASCADE ON UPDATE CASCADE,
parent INTEGER REFERENCES searchcache.queries(id) ON DELETE CASCADE ON UPDATE CASCADE,
UNIQUE(child,parent));

create or replace function searchcache.lookup(_name TEXT)
RETURNS int
AS $$
DECLARE
_id int;
BEGIN
LOOP
	SELECT id INTO _id FROM searchcache.queries WHERE name = _name;
	IF found THEN
		RETURN _id;
	END IF;
	BEGIN
		INSERT INTO searchcache.queries (name) VALUES (_name) RETURNING id INTO _id;
		RETURN _id;
	EXCEPTION
		WHEN unique_violation THEN
			-- do nothing
	END;
END LOOP;
END;
$$ language 'plpgsql';

create or replace function searchcache.reduce(_at TEXT, _bt TEXT, _op TEXT)
RETURNS text
AS $$
DECLARE
_ab TEXT;
_a int DEFAULT searchcache.lookup(_at);
_b int DEFAULT searchcache.lookup(_bt);
_abid INTEGER;
BEGIN
	_ab := 's' || _a || '_' || _b;
	RAISE NOTICE '% + % => %', _at, _bt, _ab;
	IF EXISTS (SELECT 1 FROM searchcache.queries WHERE name = _ab) THEN
		RETURN _ab;
	END IF;
	EXECUTE 'CREATE TABLE searchcache.' || _ab || ' AS SELECT id FROM searchcache.' || _at || ' ' || _op || ' ' || 'SELECT id FROM searchcache.' || _bt;
	_abid = searchcache.lookup(_ab);
	INSERT INTO searchcache.tree (child,parent) VALUES (_a, _abid);
	INSERT INTO searchcache.tree (child,parent) VALUES (_b, _abid);
	-- when unique violation...?
	RETURN _ab;
END;
$$ language 'plpgsql';

create or replace function searchcache.one_tag(_tag bigint)
RETURNS text
AS $$
DECLARE
_result text;
BEGIN
	_result := 't' || _tag::text;
	IF _result IS NULL THEN
		 RAISE EXCEPTION 'fail';
	END IF;
	IF EXISTS (SELECT 1 FROM searchcache.queries WHERE name = _result) THEN
		RETURN _result;
	END IF;
	EXECUTE 'CREATE TABLE searchcache.' || _result || ' AS SELECT unnest(neighbors) AS id FROM things WHERE id = $1' USING _tag;
	INSERT INTO searchcache.tree (child,parent) VALUES (searchcache.lookup(_result), NULL);
	RETURN _result;
END;
$$ language 'plpgsql';

create or replace function searchcache.reduce_implications(_result text, _tag bigint, _op text)
RETURNS text
AS $$
DECLARE
_subresult text;
BEGIN
		FOR _tag IN SELECT implications FROM implications(_tag) ORDER BY implications LOOP
			IF _subresult IS NULL THEN
				_subresult := searchcache.one_tag(_tag);
				IF _result IS NULL THEN
					 _result := _subresult;
				END IF;
			ELSE
				_subresult := searchcache.reduce(_result, searchcache.one_tag(_tag), 'UNION');
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
_result text;
_negresult text;
_tag bigint;
BEGIN
	FOREACH _tag IN ARRAY _posi LOOP
		_result := searchcache.reduce_implications(_result, _tag, 'INTERSECT');
	END LOOP;
	FOREACH _tag IN ARRAY _nega LOOP
		_negresult := searchcache.reduce_implications(_negresult, _tag, 'UNION');
	END LOOP;
	IF _negresult IS NOT NULL THEN
		 _result := searchcache.reduce(_result,_negresult,'EXCEPT');
	END IF;
	return _result;
END;
$$
language 'plpgsql';


create or replace function searchcache.really_expire(_query int)
RETURNS void
AS $$
DECLARE
_name text;
BEGIN
	 DELETE FROM searchcache.tree WHERE child = _query;
	 SELECT name INTO _name FROM searchcache.queries WHERE id = _query;
	 DELETE FROM searchcache.queries WHERE id = _query;
	 EXECUTE 'DROP TABLE ' || _name || ' CASCADE';
END
$$ LANGUAGE 'plpgsql';

create or replace function searchcache.follow_expire(_query int)
RETURNS int
AS $$
DECLARE
_count int;
_sub int;
BEGIN
	FOR _sub IN SELECT parent FROM searchcache.tree WHERE parent = _query LOOP
	 		_count := _count + searchcache.follow_expire(_sub);
	 END LOOP;
	 PERFORM searchcache.really_expire(_query);
	 RETURN _count;
END;
$$ language 'plpgsql';

create or replace function searchcache.expire(_newtags bigint[])
RETURNS int
AS $$
DECLARE
_count int;
_base int;
_basequeries text[] DEFAULT array(SELECT id FROM searchcache.queries INNER JOIN unnest(ARRAY[_newtags]) AS tag ON queries.name = 't' || tag.tag);
BEGIN
	FOR _base IN SELECT child FROM searchcache.tree WHERE child = ANY(_newtags) LOOP
		_count := _count + searchcache.follow_expire(_base);
		PERFORM searchcache.really_expire(_base);
	END LOOP;
	RETURN _count;
END;
$$ language 'plpgsql';
