CREATE TABLE blacklist (
    id SERIAL PRIMARY KEY,
    hash character varying(28) UNIQUE,
    reason text
);

--- the idea is to cut out "things" with creative queries
-- so media is its own root type, with its own sequence
-- images are not, because they're a kind of media
-- tags are their own root type too though
-- so anything making connections between media and tags, and tags and tags needs two intermediary tables
-- and to request both media and tags one must join media and tags, can't just select from things
-- root tables:
-- sources, media, tags
-- tags and tags must connect many-to-many
-- tags and media must connect many-to-many 
--    (1 image can have many tags, and 1 tag can have many images)
-- media and sources must connect one-to-many
-- media and author? many-to-many? or a tag?
-- a tag for now

-- avoid use of arrays because of the hassles of cleanup + set operations
-- with a "media" row in sources you can delete sources for a given media automatically
-- and no media can have sources that don't exist
-- with a "sources" array in media, you might end up with sources listed that are deleted
-- or sources without media.

CREATE TABLE media (
    id SERIAL PRIMARY KEY,
    name text,
    hash character(28) UNIQUE,
    -- sorting key, needs to be unique, should work if we use clock_timestamp
    added timestamp with time zone DEFAULT clock_timestamp() UNIQUE,
    -- these are just info about the underlying media
    created timestamp with time zone,
    modified timestamp with time zone DEFAULT clock_timestamp(),
    -- this is when it was thumbnailed last
    thumbnailed timestamp with time zone,
    size integer,
    type text,
    md5 character(32) UNIQUE,
    phash uuid
);

CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    media INTEGER REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
    checked timestamp with time zone DEFAULT clock_timestamp() UNIQUE
);

CREATE TABLE urisources (
    id INTEGER REFERENCES sources(id) ON DELETE CASCADE ON UPDATE CASCADE,
    uri text NOT NULL UNIQUE,
    code integer
);

CREATE TABLE filesources (
    id integer PRIMARY KEY REFERENCES sources(id) ON DELETE CASCADE ON UPDATE CASCADE,
    path text UNIQUE
);

CREATE TABLE images (
    id INTEGER PRIMARY KEY REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
    animated boolean,
    width integer,
    height integer,
    ratio real
);

CREATE TABLE videos (
    id INTEGER REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
    width integer,
    height integer,
    fps double precision,
    vcodec text,
    acodec text,
    container text
);

CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name text UNIQUE
);

CREATE TABLE tagtags (
    red INTEGER REFERENCES tags(id) ON DELETE CASCADE ON UPDATE CASCADE,
    blue INTEGER REFERENCES tags(id),
    UNIQUE(red,blue)
);


CREATE TABLE mediaTags (
    red INTEGER REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
    blue INTEGER REFERENCES tags(id),
    UNIQUE(red,blue)
);

CREATE TABLE tagFrequency (
       id INTEGER PRIMARY KEY REFERENCES tags(id);
       -- index on count?
       count INTEGER DEFAULT 0 NOT NULL;
);     

CREATE OR REPLACE FUNCTION findMediaForTags(_posi int[], _nega int[], _offset int, _limit int) RETURNS SETOF INT AS
$$
DECLARE
_id int;
_zeroposi bool;
_pos int DEFAULT 0;
_besttag int;
BEGIN
        _zeroposi := array_length(_posi) == 0
        IF NOT _zeroposi THEN
            _besttag := CASE WHEN EXISTS(SELECT id FROM tagfrequency WHERE _posi @> ARRAY[id])
                     THEN
                            (SELECT id FROM tagfrequency WHERE
                                 _posi @> ARRAY[id] AND
                                 count = (SELECT MIN(count) FROM tagfrequency where _posi @> ARRAY[id])
                            LIMIT 1)
                     ELSE
                            _posi[0]
                     END;
        END IF;
        FOR _id IN SELECT id FROM media
            INNER JOIN mediaTags ON mediaTags.red = media.id WHERE
            CASE
                WHEN _zeroposi THEN
                     -- just search all media excluding negatags
                     NOT _nega @> ARRAY[blue]
                ELSE
                     blue = _besttag
                END;
        LOOP
            -- if all the other tags also exist for _id then... bom
        END LOOP;


_posi[0]
                             
                  media.blue 
                media.blue IN (
               
        if array_length(posi) == 0 then
           
             
        
END
$$ language 'plpgsql';

-- extra stuff below here


CREATE TABLE comics (
    id SERIAL PRIMARY KEY,
    title text UNIQUE,
    description text,
    added timestamp with time zone DEFAULT clock_timestamp(),
    source INTEGER REFERENCES sources(id)
);

CREATE TABLE comicpage (
    id SERIAL PRIMARY KEY,
    comic INTEGER REFERENCES comics(id) ON DELETE CASCADE ON UPDATE CASCADE,
    which INTEGER,
    medium INTEGER REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE(comic,which)
);

CREATE TABLE desktops (
    id INTEGER REFERENCES images(id) ON DELETE CASCADE ON UPDATE CASCADE,
    selected timestamp with time zone DEFAULT clock_timestamp() NOT NULL
);

CREATE TABLE dupes (
    id SERIAL PRIMARY KEY,
    medium INTEGER REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
    hash character varying(28) UNIQUE,
    inferior boolean DEFAULT false,
);


CREATE TABLE parsequeue (
    id SERIAL PRIMARY KEY,
    added timestamp with time zone DEFAULT now() NOT NULL UNIQUE,
    uri text UNIQUE,
    tries integer DEFAULT 0,
    done boolean DEFAULT false
);


CREATE TABLE uzers (
    id SERIAL PRIMARY KEY,
    ident text UNIQUE,
    rescaleimages boolean DEFAULT true,
    defaulttags boolean DEFAULT false
);

CREATE TABLE uploads (
    uzer INTEGER REFERENCES uzers(id) ON DELETE CASCADE ON UPDATE CASCADE,
    media INTEGER REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
    checked timestamptz default clock_timestamp(),
    UNIQUE(uzer,media) -- catch dupe uploads
);
CREATE TABLE uzertags (
    tag INTEGER REFERENCES tags(id) ON DELETE CASCADE ON UPDATE CASCADE,
    uzer INTEGER REFERENCES uzers(id) ON DELETE CASCADE ON UPDATE CASCADE,
    nega boolean DEFAULT false,-
    UNIQUE(tag,uzer)
);
CREATE TABLE visited (
    uzer integer REFERENCES uzers(id) ON DELETE CASCADE ON UPDATE CASCADE,
    medium integer REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
    visited timestamptz DEFAULT clock_timestamp() UNIQUE,
    visits integer DEFAULT 0,
    UNIQUE(uzer,medium)
);

SET search_path = resultcache, pg_catalog;

CREATE TABLE resultcache.queries (
    id SERIAL PRIMARY KEY,
    digest text UNIQUE,
    created timestamp with time zone DEFAULT clock_timestamp()
);

CREATE INDEX bytype ON media USING btree (type);
CREATE INDEX bysources ON sources(media);
CREATE INDEX byoldest ON media USING btree (created);

CREATE INDEX tagsearch ON tagtags(red);

CREATE TRIGGER expiretrigger AFTER INSERT OR DELETE OR UPDATE ON media FOR EACH STATEMENT EXECUTE PROCEDURE resultcache.expirequeriestrigger();

CREATE TRIGGER tagexpiretrigger AFTER INSERT OR DELETE OR UPDATE ON tags FOR EACH STATEMENT EXECUTE PROCEDURE resultcache.expirequeriestrigger();


