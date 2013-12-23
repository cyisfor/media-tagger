CREATE TABLE queryOffsets(
    posi bigint[],
    nega bigint[],
    ioffset int,
    ooffset int,
    created timestamptz DEFAULT clock_timestamp(),
    UNIQUE(posi,nega,ioffset),
    UNIQUE(posi,nega,ooffset),
    UNIQUE(created)
);

CREATE INDEX Posinega ON queryOffsets(posi,nega);

-- must do this with every thing created
-- UPDATE queryOffsets SET ooffset = ooffset + 1;
CREATE OR REPLACE FUNCTION advanceOffsets() RETURNS trigger AS $$
BEGIN
    UPDATE queryOffsets SET ooffset = ooffset + 1;
END
$$ language 'plpgsql';

CREATE TRIGGER advanceOffsets AFTER INSERT ON things FOR EACH ROW EXECUTE PROCEDURE advanceOffsets();

CREATE OR REPLACE FUNCTION listMedia(_posi bigint[], _nega bigint[], _offset int, _limit int) RETURNS SETOF bigint AS $$
DECLARE
_ioffset int;
_ooffset int;
_maxoffset int;
_oldbottom int;
_page int DEFAULT 0;
_base RECORD;
_derp bigint[];
BEGIN
    -- get the real offset in media by the 
    _ioffset := _offset;
    SELECT count(id) INTO _maxoffset FROM things;
    SELECT ooffset,ioffset INTO _ooffset,_oldbottom FROM queryOffsets WHERE posi = _posi AND nega = _nega AND ioffset <= _ioffset ORDER BY ioffset LIMIT 1;
    IF found THEN
        _ioffset := _ioffset - _oldbottom;
    ELSE
        _ooffset := 0;
    END IF;
    LOOP
        IF _ooffset > _maxoffset THEN
            RETURN;
        END IF;
        FOR _base IN SELECT id FROM media ORDER BY added DESC OFFSET _ooffset LIMIT 10000 LOOP
            _ooffset := _ooffset + 1;
            WITH RECURSIVE getneighb(id, depth) AS ( 
                    SELECT id, 1 FROM things WHERE id = _base.id 
                    UNION ALL SELECT things.id,depth+1 FROM getneighb, 
                            things INNER JOIN tags ON things.id = tags.id
                        WHERE things.neighbors @> ARRAY[getneighb.id]
                        AND depth < 3)
                SELECT array_agg(id) INTO _derp FROM getneighb; 
            RAISE NOTICE 'neighbors % %',_derp,_nega;
            IF (NOT (_nega && _derp)) AND (_posi <@ _derp) THEN
                -- blah blah insert a new query offset for this query
                LOOP
                    SELECT ooffset INTO _ooffset FROM queryOffsets WHERE posi = _posi ANd nega = _nega AND ioffset = _ioffset;
                    IF found THEN
                        EXIT;
                    ELSE
                        BEGIN
                            INSERT INTO queryOffsets (posi,nega,ioffset,ooffset) VALUES (_posi,_nega,_ioffset,_ooffset);
                            EXIT;
                        EXCEPTION WHEN unique_violation THEN
                            -- do nothing, try the update again
                        END;
                    END IF;
                END LOOP;

                RETURN NEXT _base.id;
                _ioffset := _ioffset + 1;
                _limit := _limit - 1;
                IF _limit <= 0 THEN
                    RETURN;
                END IF;
            END IF;
        END LOOP;
        if _ooffset = 0 THEN
            RETURN;
        END IF;
    END LOOP;
END;
$$ language 'plpgsql';
