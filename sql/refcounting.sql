CREATE TABLE IF NOT EXISTS irdstate (
lastsucc INTEGER PRIMARY KEY REFERENCES things(id)
);

CREATE OR REPLACE FUNCTION refcountingsetup() RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
	-- extra layer of select in here, because aggregate returns one NULL if 0 values
    INSERT INTO irdstate SELECT min FROM (SELECT min(id) FROM things where 0 = (SELECT count(*) from irdstate)) meep where meep.min IS NOT NULL;
	-- ALTER TABLE things ADD COLUMN refs integer not null default 0;
	RAISE NOTICE 'ref column created';
END;
$$;

----------------------------------

CREATE OR REPLACE FUNCTION refcountingdiscover() RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
_old INTEGER;
_max INTEGER;
_id INTEGER;
_count int default 0;
BEGIN
	--	LOCK TABLE things IN ACCESS EXCLUSIVE MODE;
	SELECT lastsucc INTO _max FROM irdstate;

	FOR _id IN UPDATE things SET refs = (SELECT COUNT(*) FROM things thing2 WHERE thing2.neighbors @> ARRAY[things.id])
	FROM (
	  SELECT id, (row_number() OVER (ORDER BY id)) FROM things
	  WHERE refs = 0 AND things.id > (select lastsucc from irdstate)
	  ORDER BY id
	  LIMIT 1000) sub
	WHERE sub.id = things.id
	RETURNING things.id LOOP
			  _max := GREATEST(_max,_id);
			  _count := _count + 1;
	END LOOP;
	
	UPDATE irdstate SET lastsucc = _max;
	RETURN _count;
END;
$$;
----------------------------

CREATE OR REPLACE FUNCTION update_references() RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
	UPDATE things SET refs = refs + 1 WHERE id IN (SELECT unnest(NEW.neighbors) EXCEPT SELECT unnest(OLD.neighbors));
	UPDATE things SET refs = refs - 1 WHERE id IN (SELECT unnest(OLD.neighbors) EXCEPT SELECT unnest(NEW.neighbors));
	RETURN NEW;	
END;
$$;

CREATE OR REPLACE FUNCTION add_references() RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
	  UPDATE things SET refs = refs + 1 WHERE id = ANY(NEW.neighbors);
	  RETURN NEW;	
END;
$$;

CREATE OR REPLACE FUNCTION remove_references() RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
	  UPDATE things SET refs = refs - 1 WHERE id = ANY(OLD.neighbors);
	  RETURN OLD;
END;
$$;

CREATE OR REPLACE FUNCTION refcountingfinish() RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
	DROP TABLE irdstate;
	CREATE INDEX goners ON things(refs) WHERE refs = 0;
	RAISE NOTICE 'index of 0-refs created';

	CREATE TRIGGER updaterefs AFTER UPDATE ON things FOR EACH ROW EXECUTE PROCEDURE update_references();

	CREATE TRIGGER insrefs AFTER INSERT ON things FOR EACH ROW EXECUTE PROCEDURE add_references();

	CREATE TRIGGER delrefs AFTER DELETE ON things FOR EACH ROW EXECUTE PROCEDURE remove_references();
	RAISE NOTICE 'triggers created';
END;
$$;
