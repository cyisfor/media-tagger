BEGIN;
CREATE TABLE oldcomplexity AS SELECT id,complexity FROM tags;
UPDATE tags SET complexity = 0;
UPDATE tags SET complexity = 1 where name LIKE '%:%';
COMMIT;
