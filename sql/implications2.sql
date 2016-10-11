BEGIN;

CREATE TABLE tag_tags (
id serial primary key,
red bigint NOT NULL REFERENCES tags(id) ON UPDATE CASCADE ON DELETE CASCADE,
blue bigint NOT NULL REFERENCES tags(id) ON UPDATE CASCADE ON DELETE CASCADE,
UNIQUE(red,blue));

INSERT INTO tag_tags (red,blue) SELECT red.id, blue.id FROM tags AS red LEFT OUTER JOIN tags AS blue ON red.id IN (select unnest(neighbors) FROM things where things.id = blue.id);
COMMIT;
