CREATE OR REPLACE FUNCTION mergeSourceURI(_src int, _dsturi text) RETURNS void AS $$
DECLARE
_dst int;
BEGIN
    --    raise notice '%',_src;
    SELECT id INTO _dst FROM urisources WHERE uri = _dsturi;
    IF FOUND THEN
       UPDATE things SET neighbors = array(SELECT unnest(neighbors) UNION SELECT _dst EXCEPT SELECT _src) WHERE neighbors @> ARRAY[_src::bigint];
       DELETE FROM sources where id = _src;
    ELSE
        UPDATE urisources SET uri = _dsturi WHERE id = _src;
    END IF;
END;
$$ language 'plpgsql';
