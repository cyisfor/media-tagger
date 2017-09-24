CREATE TABLE lastCheckedForDupe (
-- not references media, since this needs to get > media ids.
             id INTEGER PRIMARY KEY,
             sentinel BOOLEAN UNIQUE NOT NULL DEFAULT FALSE);

INSERT INTO lastCheckedForDupe SELECT min(id)-1 FROM media;

CREATE TABLE possibleDupes (
    id SERIAL PRIMARY KEY,
    sis BIGINT REFERENCES media(id) ON DELETE CASCADE,
    bro BIGINT REFERENCES media(id) ON DELETE CASCADE,
    dist float4 NOT NULL,
UNIQUE(sis,bro));

--BEGIN;
CREATE TABLE dupeCheckPosition (
bottom INTEGER PRIMARY KEY NOT NULL DEFAULT 0, -- REFERENCES media(id) ON DELETE RESTRICT meh!
pendingbottom INTEGER,
top INTEGER,
sentinel BOOLEAN UNIQUE NOT NULL DEFAULT FALSE
);

INSERT INTO dupeCheckPosition (bottom) SELECT min(id)-1 FROM media;
-- CREATE RULE dupeCheckNotEmpty AS
-- ON DELETE TO media DO ALSO
--    UPDATE dupeCheckPosition SET bottom = (SELECT min(media.id) FROM media where media.id > bottom);
-- INSERT INTO dupeCheckPosition (id,bottom) SELECT 0,MIN(id) FROM media;
-- COMMIT;
-- meh!

CREATE TABLE dupesNeedRecheck(
id BIGINT PRIMARY KEY REFERENCES media(id) ON DELETE CASCADE);

--UPDATE dupeCheckPosition SET bottom = COALESCE(GREATEST((SELECT MAX(sis) FROM possibleDupes),(SELECT MAX(bro) FROM possibleDupes),bottom),bottom);
-- mehhh

DELETE FROM possibleDupes WHERE sis IN (select ID from media where pHashFail) AND bro IN (select ID from media where pHashFail);

-- go from max image down
-- check from last checked position, comparing with all images below it.
-- this works when new images are added

CREATE TYPE dupe_result AS (id INTEGER, dupes INT[], elapsed interval);

CREATE OR REPLACE FUNCTION findDupes(_threshold float4, _timeout interval, _maxrows INTEGER DEFAULT -1) RETURNS SETOF dupe_result AS $$
DECLARE
_sis record;
_bro record;
_count INTEGER DEFAULT 0;
_result dupe_result;
_bottom INTEGER;
_now TIMESTAMPTZ;
_start TIMESTAMPTZ;
_last TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;
BEGIN
	IF pendingbottom IS NULL FROM dupeCheckPosition THEN
		 UPDATE dupeCheckPosition SET pendingbottom = (SELECT MAX(id) FROM media);
	END IF;
    raise notice 'top % bottom %', (select to_hex(top) from dupeCheckPosition), (select to_hex(bottom) from dupeCheckPosition);
    FOR _sis IN SELECT media.id,phash FROM media
		    LEFT OUTER JOIN possibleDupes ON media.id = possibleDupes.sis
				WHERE 
          phash != 0  AND
          phash IS NOT NULL AND 
          possibleDupes.id IS NULL
				AND media.id > (SELECT bottom FROM dupeCheckPosition)
        -- note: bottom should only be set when done traversing
        -- don't set bottom w/out checking ALL media below it
        AND ((SELECT top FROM dupeCheckPosition) IS NULL
                OR media.id < (SELECT top FROM dupeCheckPosition))
        -- top probably shouldn't be set, but when incrementally traversing
        -- since postgres is retarded and cannot do loops outside of transactions
        -- set top lower each time, until done. then set top to NULL
				ORDER BY media.id DESC LIMIT 1000
    LOOP
			_result.id := _sis.id;
			_start := clock_timestamp();
      FOR _bro IN SELECT media.id,pHash as hash,hammingfast(phash,_sis.phash)
					AS dist FROM media
					LEFT OUTER JOIN nadupes ON media.id = nadupes.bro AND _sis.id = nadupes.sis
          WHERE nadupes.id IS NULL
          AND phash != 0
          AND phash IS NOT NULL
          AND media.id < _sis.id
          AND hammingfast(phash,_sis.phash) < _threshold
      LOOP
				_result.dupes := array_append(_result.dupes,_bro.id);
				-- raise notice 'dupe % % %',to_hex(_sis.id),to_hex(_bro.id),_bro.dist;
				BEGIN
					INSERT INTO possibleDupes (sis,bro,dist) VALUES (_sis.id,_bro.id,_bro.dist);
        EXCEPTION
					WHEN unique_violation THEN
						RAISE NOTICE 'already checked (thisisbad) %',to_hex(_sis.id);
        END;
			END LOOP;
						
			UPDATE dupeCheckPosition SET top = _sis.id;
			DELETE FROM dupesNeedRecheck WHERE id = _sis.id;
			RETURN NEXT _result;
			_result.dupes := '{}'::int[];
			_now := clock_timestamp();
			_result.elapsed = _now - _start;
			--raise NOTICE 'tested % %', to_hex(_sis.id),extract(epoch from (_now-_start));

			IF _now - _last > _timeout THEN
				 RETURN;
			END IF;
			IF _maxrows > 0 THEN
				 _count := _count + 1;
				 IF _count > _maxrows THEN
				 		RETURN;
				 END IF;
			END IF;
    END LOOP;
END
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION recheckFindDupes(_threshold float4) RETURNS int AS $$
DECLARE
_sis record;
_bro record;
_bottom INTEGER;
_count int DEFAULT 0;
BEGIN
	FOR _sis IN SELECT media.id,phash FROM media WHERE phash IS NOT NULL AND
    media.id IN (select id from dupesneedrecheck) LIMIT 1000

    LOOP
        FOR _bro IN SELECT media.id,pHash as hash, hammingfast(phash,_sis.phash) AS dist FROM media
    LEFT OUTER JOIN dupesneedrecheck ON media.id = dupesneedrecheck.id
            WHERE phash IS NOT NULL AND dupesneedrecheck.id IS NULL
              AND media.id != _sis.id
--              AND hammingfast(phash,_sis.phash) < _threshold
        LOOP
            BEGIN
        INSERT INTO possibleDupes (sis,bro,dist) VALUES (_sis.id,_bro.id,_bro.dist);
        _count := _count + 1;
        EXCEPTION
                 WHEN unique_violation THEN
                 RAISE NOTICE 'already checked % %',_sis.id,_bro.id;
        END;
        END LOOP;
    DELETE FROM dupesNeedRecheck WHERE id = _sis.id;
    RAISE NOTICE 'finished rechecking %',_sis.id;
    END LOOP;
    RETURN _count;
END
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION findDupesDone() RETURNS VOID AS $$
BEGIN
  UPDATE dupeCheckPosition SET
				 bottom = pendingbottom,
				 top = NULL,
				 pendingbottom = NULL
			WHERE pendingbottom IS NOT NULL;
END
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION findEmptyDupes(_threshold float4) RETURNS int AS $$
DECLARE
_sis record;
_bro record;
_bottom INTEGER;
_count int DEFAULT 0;
BEGIN
    FOR _sis IN SELECT id,mh_hash FROM media
        WHERE
                id NOT IN (select sis from possibleDupes) AND
                id > (select id from lastCheckedForDupe) AND
        mh_hash IS NOT NULL AND
        pHash = 0
                ORDER BY id ASC
    LOOP
        FOR _bro IN SELECT media.id,mh_hash, hamming(mh_hash,_sis.mh_hash) AS dist FROM media
        LEFT OUTER JOIN nadupes ON media.id = nadupes.bro AND media.id = nadupes.sis
        WHERE nadupes.id IS NULL AND
              mh_hash IS NOT NULL AND
              pHash = 0 AND
                            not pHashFail AND
              hamming(mh_hash,_sis.mh_hash) < _threshold
         LOOP
            BEGIN
              RAISE NOTICE 'lost dupe sis % bro % dist %',_sis.id,_bro.id,_bro.dist;

              INSERT INTO possibleDupes (sis,bro,dist) VALUES (_sis.id,_bro.id,_bro.dist);
              _count := _count + 1;
            EXCEPTION
                WHEN unique_violation THEN
                    RAISE NOTICE 'already checked (thisisbad) %',_sis.id; 
            END;
         END LOOP;
                 UPDATE lastCheckedForDupe set id = _sis.id;
    END LOOP;
    RETURN _count;
END
$$ language 'plpgsql';

