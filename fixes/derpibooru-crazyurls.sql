drop function herpderp();
create or replace function herpderp() returns VOID as $$
DECLARE
_old int;
_new int;
_newuri text;
BEGIN
    FOR _old,_newuri IN SELECT id,regexp_replace(uri,E'(.*/[0-9]+).*(\\.[^?]*)(?:\\?.*)?$',E'\\1\\2') from urisources where uri ~ 'http.*derpicdn.net.*_.*' LIMIT 1000 LOOP
        SELECT id INTO _new FROM urisources WHERE uri = _newuri;
        IF NOT FOUND THEN
           INSERT INTO sources DEFAULT VALUES RETURNING id INTO _new;
           INSERT INTO urisources (id,uri) VALUES (_new,_newuri);
           --RAISE NOTICE 'Creating new %',  _new;
        END IF;
        --RAISE NOTICE 'Fixing %',_newuri;
        PERFORM mergeSources(_new, _old);
    END LOOP;
END
$$ language 'plpgsql';

select herpderp();
