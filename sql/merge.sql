DROP FUNCTION mergeSources(int,int,text);

CREATE OR REPLACE FUNCTION mergeSources(_dest int, _loser int, _uri text) RETURNS text AS $$
BEGIN
    IF _dest != _loser THEN
        UPDATE media SET sources = array(SELECT unnest(sources) UNION SELECT _dest EXCEPT SELECT _loser) WHERE sources @> ARRAY[_loser];
        UPDATE comics SET source = _dest WHERE source = _loser;
        DELETE FROM sources WHERE id = _loser;
        UPDATE urisources SET uri = _uri WHERE id = _dest;
        RETURN _dest || ' yay ' || _uri;
    END IF;
    UPDATE urisources SET uri = _uri WHERE id = _dest;
    RETURN 'nope ' || _uri;
END;
$$ language 'plpgsql';

drop table tempsources;

CREATE TEMPORARY TABLE tempsources (
    id INTEGER PRIMARY KEY,
    uri TEXT
);

INSERT INTO tempsources (id,uri) SELECT id,regexp_replace(uri,'\?.*','') FROM urisources WHERE uri LIKE '%deviantart.com/art/%-%?%';

select * from tempsources;

SELECT mergeSources(MIN(a.id),b.id,b.uri) FROM tempsources AS a, tempsources AS b WHERE a.uri = b.uri group by b.id, b.uri;
