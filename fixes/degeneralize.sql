--DROP function degen1(_general bigint, _name text, _genrefs int);
--DROP function fixstuff();

create or replace function degen2(_interval interval) returns void language plpgsql as $$
DECLARE
_genrefs int;
_general bigint;
_name text;
_shortname text;
_ungenrefs int;
_ungen bigint;
_start timestamptz;
BEGIN
	FOR _general,_name,_genrefs IN SELECT things.id,name,refs FROM tags inner join things on tags.id = things.id WHERE name LIKE 'general:%' ORDER BY refs DESC LOOP
		IF clock_timestamp()-current_timestamp > '1 minute'::interval THEN
		   RETURN;
		 END IF;
		 
		_start := clock_timestamp();
		_shortname := substring(_name FROM length('general:')+1);
		_ungen := findTag(_shortname);
		RAISE NOTICE 'name % % %',_name,_genrefs,_ungen;

		-- ref update triggers disabled for speed
		UPDATE things SET  refs = refs + _genrefs, neighbors = array(SELECT DISTINCT unnest(array_cat(neighbors,(SELECT neighbors FROM things WHERE id = _general)))) WHERE id = _ungen RETURNING refs INTO _ungenrefs;
		IF clock_timestamp()-_start > '10 seconds'::interval THEN
		   RAISE NOTICE 'merge %',_ungenrefs;
		END IF;
		WITH updoot AS (UPDATE things SET neighbors =  array_append(array_remove(neighbors,_general),_ungen) WHERE neighbors @> ARRAY[_general] RETURNING 1)
			SELECT count(*) INTO _ungenrefs FROM updoot;
		IF clock_timestamp()-_start > '10 seconds'::interval THEN
		   RAISE NOTICE 'fixneighb %',_ungenrefs;
		END IF;
		DELETE FROM things WHERE id = _general;
	END LOOP;
END;
$$;

create or replace function degeneralize(_interval interval DEFAULT '1 minute'::interval) returns void language plpgsql as $$
BEGIN
	LOCK TABLE things IN ACCESS EXCLUSIVE MODE;
	ALTER TABLE things DISABLE TRIGGER ALL;
	PERFORM degen2(_interval);
	ALTER TABLE things ENABLE TRIGGER ALL;
END;
$$;
