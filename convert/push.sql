LISTEN info;
BEGIN;
\echo 'doing tags'
COPY things (id) FROM '/dev/shm/convert/image';
CREATE TEMPORARY TABLE temptags (id integer, name text);
LISTEN info;
COPY temptags (id,name) FROM '/dev/shm/convert/tag';
-- note: cannot 'fix' the tag / image ids because they are in the image_tag thing.
CREATE TEMPORARY TABLE tempmax (id integer);
insert into tempmax (id) SELECT MAX(id) FROM things;
INSERT INTO things (id) SELECT (select id FROM tempmax)+id FROM temptags;
INSERT INTO tags (id,name) SELECT (select id from tempmax)+id,name FROM temptags;
\echo 'doing neighbors'
create temporary table tempit (image integer, tag integer);
COPY tempit (image,tag) FROM '/dev/shm/convert/it';
\echo 'calculating neighbors'
update things set neighbors = derp.tag from (select array_agg(tag+(select id from tempmax)) as tag, image from tempit group by image) as derp where things.id = derp.image;
\echo 'doing media'
CREATE TEMPORARY TABLE tempmedia (id integer, 
    name text, 
    hash character varying(28), 
    created timestamp with time zone, 
    added timestamp with time zone, 
    size integer, 
    type text, 
    md5 character(32), 
    thumbnailed timestamp with time zone, 
    animated boolean, 
    width integer, height integer, ratio real);
COPY tempmedia FROM '/dev/shm/convert/media';
-- I'm proud of this trick:
update tempmedia set added = new.added + (new.rnum - 1) * INTERVAL '1 second' FROM (SELECT id,added,row_number() over (partition by added) AS rnum FROM media) AS new WHERE new.rnum > 1 AND new.id = tempmedia.id;
-- just to be sure:
CREATE UNIQUE INDEX derp ON tempmedia(added);
DROP INDEX derp;
insert into media (id,name,hash,created,added,size,type,md5,thumbnailed) select id,name,hash,created,added,size,type,md5,thumbnailed from tempmedia;
\echo 'doing images'
insert into images (id,animated,width,height,ratio) select id,animated,width,height,ratio from tempmedia;
COMMIT;
BEGIN;
\echo 'doing sources'
CREATE TEMPORARY TABLE tempsauce (id integer, image integer, uri text, code integer, checked INTEGER);
COPY tempsauce FROM '/dev/shm/convert/sauce';
create temporary table filesauce (id integer, image integer, path text);
COPY filesauce (id, path) FROM '/dev/shm/convert/filesauce';
UPDATE filesauce SET image = id;

\echo 'Loaded sources, importing...'
UPDATE tempsauce set id = id - (select MIN(id) FROM tempsauce) + 1;
UPDATE filesauce set id = id + (select MAX(id) FROM tempsauce)
    - (select MIN(id) FROM filesauce) + 1;
-- make the sources w/ different id's have the same id but different images
update tempsauce set id = derp.derp from (select id,min(id) over (partition by uri) as derp from tempsauce) as derp where derp.id = tempsauce.id;
update filesauce set id = derp.derp from (select id,min(id) over (partition by path) as derp from filesauce) as derp where derp.id = filesauce.id;
UPDATE media SET sources = sauce FROM (
    SELECT array_agg(id) AS sauce,image FROM tempsauce GROUP BY image
    UNION
    SELECT array_agg(id) AS sauce,image FROM filesauce GROUP BY image
    ) AS derp WHERE derp.image = media.id;
-- now delete the duplicate id rows...
delete from tempsauce where ctid in (select ctid from (select ctid, row_number() over (partition by id) as rnum from tempsauce) s where rnum > 1);
delete from filesauce where ctid in (select ctid from (select ctid, row_number() over (partition by id) as rnum from filesauce) s where rnum > 1);
insert into sources (id) select id from filesauce where id not in (select id from sources);
insert into filesources (id,path) select id,path from filesauce;
insert into sources (id,checked) SELECT id,TIMESTAMP WITH TIME ZONE 'epoch' + checked / 1000 * INTERVAL '1 second' FROM tempsauce;
insert into urisources (id,uri,code) SELECT id,uri,code FROM tempsauce;
COMMIT;
BEGIN;
\echo 'sources imported, cleaning up sequence counters'
select setval('things_id_seq',MAX(id)) FROM things;
select setval('sources_id_seq',MAX(id)) FROM sources;
COMMIT;
BEGIN;
\echo 'Dropping tables'
DROP TABLE IF EXISTS filesauce;
DROP TABLE IF EXISTS tempsauce;
DROP TABLE IF EXISTS tempmedia;
DROP TABLE IF EXISTS tempmax;
DROP TABLE IF EXISTS temptags;
DROP TABLE IF EXISTS tempit;
COMMIT;
\echo 'Done!'
