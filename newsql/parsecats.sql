CREATE TYPE relation (
  category regclass;
  id integer;
 );

CREATE OR REPLACE FUNCTION realizeTags(_categories text? regclass? int?[], _names text[], _create boolean DEFAULT TRUE, _tname regclass DEFAULT NULL) RETURNS regclass AS $$
BEGIN
        IF _tname IS NULL THEN;
           _tname = 'relations' || random() || clock_timestamp();
        END IF;
        EXECUTE 'CREATE TEMPORARY TABLE ' || _tname '(item relation UNIQUE)';

        FOR _i IN 0 .. array_length(_categories,1) LOOP;
            

        RETURN _tname;
        
        
