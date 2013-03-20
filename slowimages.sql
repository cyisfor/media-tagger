-------------------------------------------------------------------------
------ below is just setting up a test db

BEGIN;

DROP TABLE things CASCADE;
DROP TABLE images CASCADE;
DROP TABLE tags CASCADE;
DROP TABLE connections CASCADE;

CREATE TABLE things(id BIGSERIAL PRIMARY KEY);
CREATE TABLE images(id bigint PRIMARY KEY REFERENCES things(id) ON DELETE CASCADE ON UPDATE CASCADE,
    name TEXT UNIQUE);
CREATE TABLE tags(id bigint PRIMARY KEY REFERENCES things(id) ON DELETE CASCADE ON UPDATE CASCADE,
    name TEXT UNIQUE);
CREATE TABLE connections(
    red bigint REFERENCES things(id) ON DELETE CASCADE ON UPDATE CASCADE,
    blue bigint REFERENCES things(id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE(red,blue));

CREATE INDEX redcon ON connections(red);
CREATE INDEX bluecon ON connections(blue);

WITH thing AS (INSERT INTO things DEFAULT VALUES RETURNING id)
    INSERT INTO images(id,name) SELECT id,'ferret in tube.gif' FROM thing;
WITH thing AS (INSERT INTO things DEFAULT VALUES RETURNING id)
    INSERT INTO images(id,name) SELECT id,'another ferret in tube.gif' FROM thing;
WITH thing AS (INSERT INTO things DEFAULT VALUES RETURNING id)
    INSERT INTO images(id,name) SELECT id,'ferret mid jump.jpg' FROM thing;
WITH thing AS (INSERT INTO things DEFAULT VALUES RETURNING id)
    INSERT INTO images(id,name) SELECT id,'ferretspin.gif' FROM thing;
WITH thing AS (INSERT INTO things DEFAULT VALUES RETURNING id)
    INSERT INTO images(id,name) SELECT id,'horse in tube.gif' FROM thing;

WITH thing AS (INSERT INTO things DEFAULT VALUES RETURNING id)
    INSERT INTO tags(id,name) SELECT id,'ferret' FROM thing;
WITH thing AS (INSERT INTO things DEFAULT VALUES RETURNING id)
    INSERT INTO tags(id,name) SELECT id,'species' FROM thing;
WITH thing AS (INSERT INTO things DEFAULT VALUES RETURNING id)
    INSERT INTO tags(id,name) SELECT id,'species:ferret' FROM thing;
WITH thing AS (INSERT INTO things DEFAULT VALUES RETURNING id)
    INSERT INTO tags(id,name) SELECT id,'species:horse' FROM thing;
WITH thing AS (INSERT INTO things DEFAULT VALUES RETURNING id)
    INSERT INTO tags(id,name) SELECT id,'tube' FROM thing;
WITH thing AS (INSERT INTO things DEFAULT VALUES RETURNING id)
    INSERT INTO tags(id,name) SELECT id,'animated' FROM thing;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'species:ferret'),
        (SELECT id FROM tags WHERE name = 'ferret') 
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'species:ferret'),
        (SELECT id FROM tags WHERE name = 'species') 
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'species:horse'),
        (SELECT id FROM tags WHERE name = 'species') 
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'species:ferret'),
        (SELECT id FROM images WHERE name = 'ferret in tube.gif')
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'ferret'),
        (SELECT id FROM images WHERE name = 'another ferret in tube.gif')
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'species:ferret'),
        (SELECT id FROM images WHERE name = 'ferret mid jump.jpg')
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'species:ferret'),
        (SELECT id FROM images WHERE name = 'ferretspin.gif')
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'species:horse'),
        (SELECT id FROM images WHERE name = 'horse in tube.gif')
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'animated'),
        (SELECT id FROM images WHERE name = 'horse in tube.gif')
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'animated'),
        (SELECT id FROM images WHERE name = 'ferretspin.gif')
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'animated'),
        (SELECT id FROM images WHERE name = 'ferret in tube.gif')
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'animated'),
        (SELECT id FROM images WHERE name = 'another ferret in tube.gif')
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'tube'),
        (SELECT id FROM images WHERE name = 'horse in tube.gif')
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'tube'),
        (SELECT id FROM images WHERE name = 'ferret in tube.gif')
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'tube'),
        (SELECT id FROM images WHERE name = 'another ferret in tube.gif')
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH thing AS (INSERT INTO things DEFAULT VALUES RETURNING id)
    INSERT INTO images(id,name) SELECT id,'ferret tubes1.jpg' FROM thing;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'species:ferret'),
        (SELECT id FROM images WHERE name = 'ferret tubes1.jpg')
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'tube'),
        (SELECT id FROM images WHERE name = 'ferret tubes1.jpg')
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH thing AS (INSERT INTO things DEFAULT VALUES RETURNING id)
    INSERT INTO images(id,name) SELECT id,'ferret tubes2.jpg' FROM thing;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'species:ferret'),
        (SELECT id FROM images WHERE name = 'ferret tubes2.jpg')
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'tube'),
        (SELECT id FROM images WHERE name = 'ferret tubes2.jpg')
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;


WITH thing AS (INSERT INTO things DEFAULT VALUES RETURNING id)
    INSERT INTO tags(id,name) SELECT id,'harness' FROM thing;

WITH connection AS (INSERT INTO connections (red,blue) SELECT
        (SELECT id FROM tags WHERE name = 'harness'),
        (SELECT id FROM images WHERE name = 'ferret tubes2.jpg')
    RETURNING red,blue)
INSERT INTO connections (blue,red) SELECT red,blue FROM connection;

COMMIT;

------ above is just setting up a test db
-------------------------------------------------------------------------
\i withtags.sql
