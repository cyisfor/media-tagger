CREATE TABLE possibleDupes (
    id SERIAL PRIMARY KEY,
    sis BIGINT REFERENCES media(id) ON DELETE CASCADE,
    bro BIGINT REFERENCES media(id) ON DELETE CASCADE,
    dist float4 NOT NULL,
UNIQUE(sis,bro));

CREATE TABLE dupeCheckPosition (
    bottom BIGINT PRIMARY KEY);

INSERT INTO dupeCheckPosition VALUES (0);

CREATE OR REPLACE FUNCTION findDupes(_threshold float4) RETURNS VOID AS $$
DECLARE
_test record;
_result record;
_bottom bigint;
BEGIN
    FOR _test IN SELECT media.id,phash FROM media
        WHERE phash IS NOT NULL AND media.id > (SELECT bottom FROM dupeCheckPosition) ORDER BY media.id ASC LIMIT 1000
        LOOP
        FOR _result IN SELECT media.id,pHash as hash,hammingfast(phash,_test.phash) AS dist FROM media 
        LEFT OUTER JOIN nadupes ON media.id = nadupes.bro AND _test.id = nadupes.sis
        WHERE nadupes.id IS NULL
        AND phash IS NOT NULL AND media.id < _test.id
	AND hammingfast(phash,_test.phash) < _threshold
        LOOP
            INSERT INTO possibleDupes (sis,bro,dist) VALUES (_test.id,_result.id,_result.dist);
        END LOOP;
        UPDATE dupeCheckPosition SET bottom = _test.id;
    END LOOP;
END
$$ language 'plpgsql';

