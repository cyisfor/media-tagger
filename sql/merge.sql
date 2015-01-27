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

CREATE OR REPLACE FUNCTION mergeAdded(_a bigint, _b bigint) RETURNS VOID AS
$$
DECLARE
_aadd timestamptz;
_badd timestamptz;
BEGIN
    _aadd := COALESCE(added,modified,created) FROM media WHERE id = _a;
    IF _aadd IS NULL THEN
       _aadd := added + ('1 second'::interval * random() / 10000) FROM media WHERE
    	  id < _a AND added IS NOT NULL LIMIT 1;
   END IF;
    _badd := COALESCE(added,modified,created) FROM media WHERE id = _b;
    IF _badd IS NULL THEN
      _badd := added + ('1 second'::interval * random() / 10000) FROM media WHERE
        id < _b AND added IS NOT NULL LIMIT 1;
    END IF;
    IF _aadd IS NULL AND _badd IS NULL THEN
      _aadd = clock_timestamp();
    ELSIF _aadd IS NULL THEN
       _aadd := _badd;
    ELSE
       _aadd := GREATEST(_aadd,_badd);
    END IF;
    UPDATE media SET added = NULL WHERE id = _b;
    UPDATE media SET added = _aadd WHERE id = _a;
END
$$ language 'plpgsql';

