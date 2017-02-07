BEGIN;
SET CONSTRAINTS ALL DEFERRED;
CREATE TABLE tag_tags (
id serial primary key,
red INTEGER NOT NULL REFERENCES tags(id) ON UPDATE CASCADE ON DELETE CASCADE,
blue INTEGER NOT NULL REFERENCES tags(id) ON UPDATE CASCADE ON DELETE CASCADE,
UNIQUE(red,blue));
LOCK TABLE tag_tags IN ACCESS EXCLUSIVE MODE;

INSERT INTO tag_tags (red,blue) select tags.id,unnest(array(select things.id from things inner join tags on tags.id = things.id where neighbors @> ARRAY[tags.id])) from tags LIMIT 400;
COMMIT;
