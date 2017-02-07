create or replace function herpderp() returns SETOF text as $$
DECLARE
_source int;
_oldsource int;
_medium INTEGER;
_uri text;
_artist text;
begin
    FOR _source,_uri IN select id,uri from urisources where uri LIKE 'https://derpibooru.org/art/%' ORDER BY id DESC limit 100 LOOP
    SELECT id INTO _medium FROM media WHERE sources @> ARRAY[_source];
    SELECT substr(name,8,length(name)) into _artist from tags where id IN (select unnest(neighbors) FROM things WHERE id = _medium) AND name LIKE 'artist:%';
        IF _uri IS NULL THEN
          RAISE EXCEPTION 'uhhh %', _source;
          END IF;
        IF _artist IS NOT NULL THEN
        _uri := 'http://' || _artist || '.deviantart.com' || substr(_uri,23,length(_uri)) ;
           BEGIN
           UPDATE urisources SET uri = _uri WHERE id = _source;
           EXCEPTION
            WHEN unique_violation THEN
                 DELETE FROM sources WHERE id = _source;
                  SELECT id INTO _oldsource FROM urisources WHERE uri = _uri;
                  UPDATE media SET sources = array(SELECT unnest FROM unnest(sources) UNION SELECT _oldsource EXCEPT SELECT _source) WHERE id = _medium;
           END;
           RAISE NOTICE 'got one % %',_medium, _source;
        ELSE
           RAISE NOTICE 'no artist found for %', to_hex(_medium);
        END IF;
    END LOOP;
end
$$ language 'plpgsql';
SELECT * from herpderp();
