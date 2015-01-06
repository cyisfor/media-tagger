CREATE TABLE possibleDupes (
    id SERIAL PRIMARY KEY,
    sis BIGINT REFERENCES media(id),
    bro BIGINT REFERENCES media(id),
    dist float4 NOT NULL
UNIQUE(sis,bro));

CREATE OR REPLACE FUNCTION findDupes(_bottom bigint,_top bigint) RETURNS VOID AS $$
DECLARE
_test record;
_result record;
BEGIN
    FOR _test IN SELECT media.id,phash FROM media
        WHERE phash IS NOT NULL AND (_bottom IS NULL OR media.id > _bottom) AND (_top IS NULL OR media.id <= _top)
        LOOP
        FOR _result IN SELECT media.id,pHash as hash,hammingfast(phash,_test.phash) AS dist FROM media 
        LEFT OUTER JOIN nadupes ON media.id = nadupes.bro AND _test.id = nadupes.sis
        WHERE nadupes.id IS NULL
        AND phash IS NOT NULL AND media.id < _test.id AND hammingfast(phash,_test.phash) < 10
        LOOP
            RAISE NOTICE 'found one I found one I found one';
            INSERT INTO possibleDupes (sis,bro,dist) VALUES (_test.id,_result.id,_result.dist);
        END LOOP;
    END LOOP;
END
$$ language 'plpgsql';

