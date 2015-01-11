CREATE TABLE possibleDupes (
    id SERIAL PRIMARY KEY,
    sis BIGINT REFERENCES media(id) ON DELETE CASCADE,
    bro BIGINT REFERENCES media(id) ON DELETE CASCADE,
    dist float4 NOT NULL,
UNIQUE(sis,bro));

BEGIN;
CREATE TABLE dupeCheckPosition (
id int PRIMARY KEY,
bottom BIGINT REFERENCES media(id) ON DELETE RESTRICT
);
CREATE RULE dupeCheckNotEmpty AS
ON DELETE TO media DO ALSO
   UPDATE dupeCheckPosition SET bottom = (SELECT min(media.id) FROM media where media.id > bottom);
INSERT INTO dupeCheckPosition (id,bottom) SELECT 0,MIN(id) FROM media;
COMMIT;

CREATE TABLE dupesNeedRecheck(
id BIGINT PRIMARY KEY REFERENCES media(id) ON DELETE CASCADE);

UPDATE dupeCheckPosition SET bottom = COALESCE(GREATEST((SELECT MAX(sis) FROM possibleDupes),(SELECT MAX(bro) FROM possibleDupes),bottom),bottom);

CREATE OR REPLACE FUNCTION findDupes(_threshold float4) RETURNS int AS $$
DECLARE
_test record;
_result record;
_bottom bigint;
_count int DEFAULT 0;
BEGIN
    FOR _test IN SELECT media.id,phash FROM media
    LEFT OUTER JOIN possibleDupes ON media.id = possibleDupes.sis
    WHERE phash IS NOT NULL AND possibleDupes.id IS NULL
    AND media.id > coalesce((SELECT bottom FROM dupeCheckPosition),0) LIMIT 1000
    LOOP
            FOR _result IN SELECT media.id,pHash as hash,hammingfast(phash,_test.phash) AS dist FROM media 
            LEFT OUTER JOIN nadupes ON media.id = nadupes.bro AND _test.id = nadupes.sis
            WHERE nadupes.id IS NULL
            AND phash IS NOT NULL AND media.id < _test.id
    	AND hammingfast(phash,_test.phash) < _threshold
            LOOP
	        raise notice 'dupe % % %',_test.id,_result.id,_result.dist;
                BEGIN
			INSERT INTO possibleDupes (sis,bro,dist) VALUES (_test.id,_result.id,_result.dist);
		    	 _count := _count + 1;
		EXCEPTION
		        WHEN unique_violation THEN
			        RAISE NOTICE 'already checked %',_test.id;
		END;
            END LOOP;
    	UPDATE dupeCheckPosition SET bottom = GREATEST(bottom,_test.id);
    	DELETE FROM dupesNeedRecheck WHERE id = _test.id;
        END LOOP;
    FOR _test IN SELECT media.id,phash FROM media WHERE phash IS NOT NULL AND
    media.id IN (select id from dupesneedrecheck) LIMIT 1000
    LOOP
        FOR _result IN SELECT media.id,pHash as hash, hammingfast(phash,_test.phash) AS dist FROM media
	LEFT OUTER JOIN dupesneedrecheck ON media.id = dupesneedrecheck.id
            WHERE phash IS NOT NULL AND dupesneedrecheck.id IS NULL
      	    AND media.id != _test.id
      	    AND hammingfast(phash,_test.phash) < _threshold
        LOOP
	        BEGIN
		INSERT INTO possibleDupes (sis,bro,dist) VALUES (_test.id,_result.id,_result.dist);
		_count := _count + 1;
		EXCEPTION
     			WHEN unique_violation THEN
			     RAISE NOTICE 'already checked % %',_test.id,_result.id;
		END;
        END LOOP;
	DELETE FROM dupesNeedRecheck WHERE id = _test.id;
	RAISE NOTICE 'finished with %',_test.id;
    END LOOP;
    RETURN _count;
END
$$ language 'plpgsql';

