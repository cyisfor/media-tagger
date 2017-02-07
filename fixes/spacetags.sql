BEGIN;
CREATE OR REPLACE FUNCTION mergeTags(_good INTEGER, _bad INTEGER) RETURNS VOID AS
$$
BEGIN
  update things set neighbors = array(select unnest(neighbors) except select _bad union select _good) WHERE neighbors && ARRAY[_good,_bad];
  DELETE FROM tags WHERE id = _bad;
END
$$ language 'plpgsql';

-- SELECT ltrim(rtrim(name)),name from tags where name LIKE ' %' OR name LIKE '% ';

SELECT mergeTags(findTag(ltrim(rtrim(name))),id) from tags where name LIKE ' %' OR name LIKE '% ';
