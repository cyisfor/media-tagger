CREATE TABLE blacklist (
    id SERIAL PRIMARY KEY,
    hash character varying(28) UNIQUE,
    reason text
);

--- the idea is to cut out "things" with creative queries
-- so media is its own root type, with its own sequence
-- images are not, because they're a kind of media
-- tags are their own root type too though
-- so anything making connections between media and tags and tags needs two intermediary tables
-- and to request both media and tags one must join media and tags, can't just select from things
-- root tables:
-- sources, media, tags
-- tags and tags must connect many-to-many
-- tags and media must connect many-to-many 
--    (1 image can have many tags, and 1 tag can have many images)
-- media and sources must connect one-to-many
-- media and author? artist? many-to-many? or a tag?

-- avoid use of arrays because of the hassles of cleanup!!
-- f/i:
-- with a "media" row in sources you can delete sources for a given media automatically
-- and no media can have sources that don't exist
-- with a "sources" array in media, you might end up with sources listed that are deleted
-- or sources without media.

-- tag relationships should be "two" way, with priority to one way
-- so like, artist - artist:egophiliac could discover that artist:egophiliac is tagged 'artist'
-- but looking up artist by itself would... return artist records not images...mm...
-- different table for each 'category' of tag? 
-- artistmediatags? yeah artist - artistmedia - media, uzer - uzermedia - media etc
-- too many combinations?

-- how about semantics? D:
-- uzermedia = red, name, blue instead of uzertags = red, bluetag -> tag -> tagmedia -> media -> blue?
-- what about users tagging artists? users tagging users?
-- this is all to cut out 'things' and allow for INTEGER keys for sequential lookup, so...
-- (a, aid) -> (b, bid) pair table id with row id?
-- abtag = red(a) -> blue(b) + name ?
-- yeah, so no "mediatag" it has to be "uzermediatag" or "artistmediatag" or "mediamediatag" (related images?) or uzerartisttag
-- with a -> b being priority, so uzerartist would expect to look up artists tagged by a user not
-- users tagging an artist, but artistmediatag could expect to look up media by artist, AND
-- artist by media, since different table. ...except it's important to list who tagged what,
-- so users tagging an artist needs to be indexed too. Bah!

-- tags = words? describes = ...?
-- general dumping ground for unstructured concepts?
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,  
    name TEXT UNIQUE
);

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

CREATE INDEX bytype ON media USING btree (type);
CREATE INDEX byoldest ON media USING btree (created);

CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
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

-- includes fictional
-- "idea" of a person
CREATE TABLE people (
    id SERIAL PRIMARY KEY, 
    -- don't we need more than 4 billion people though?
    -- INCLUDING fictional characters? and dead people?
    name TEXT UNIQUE,
    description TEXT
    -- isreal boolean ?
);

CREATE TABLE uzers (
    id INTEGER REFERENCES people(id) ON DELETE CASCADE ON UPDATE CASCADE,
    rescaleimages boolean DEFAULT true,
    defaulttags boolean DEFAULT false
);

CREATE TABLE artists (
    id INTEGER REFERENCES people(id) ON DELETE CASCADE ON UPDATE CASCADE,
    -- ...?
);

CREATE TABLE verses (
    id SERIAL PRIMARY KEY,
    ident TEXT UNIQUE,
    concept TEXT,
    source INTEGER REFERENCES urisources(id),
);

CREATE TABLE acts (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE,
    description TEXT,
    sexiness INTEGER DEFAULT 0 -- uh...
);

-- things that aren't people
-- items, unnamed people, plants, etc
CREATE TABLE things (
    id SERIAL PRIMARY KEY,
    ident TEXT UNIQUE,
    description TEXT
);

-- don't worry too much about recording which user created what record
-- can make a log for that, parse the log to undo the user's destructive urges etc

CREATE SCHEMA r.relation;

CREATE TABLE r.acquiredfrom (
    medium INTEGER REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
    source INTEGER REFERENCES sources(id) ON DELETE CASCADE ON UPDATE CASCADE
    UNIQUE(medium) -- sigh
);
    

CREATE TABLE r.wantstags (
    uzer INTEGER REFERENCES uzers(id) ON DELETE CASCADE ON UPDATE CASCADE,
    tag INTEGER REFERENCES tags(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE r.uploaded (
    uzer INTEGER REFERENCES uzers(id) ON DELETE CASCADE ON UPDATE CASCADE,
    medium INTEGER REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
    checked timestamptz default clock_timestamp(),
    UNIQUE(uzer,media) -- catch dupe uploads
);

-- present tense for relations w/out a timestamp

CREATE TABLE r.webmasters (
    person INTEGER REFERENCES people(id) ON DELETE CASCADE ON UPDATE CASCADE,
    source INTEGER REFERENCES urisources(id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE(person,source)
);

CREATE TABLE r.drew (
    artist INTEGER REFERENCES artists(id) ON DELETE CASCADE ON UPDATE CASCADE,
    medium INTEGER REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
    when timestamptz,
    UNIQUE(artist,medium)
);

-- this would be better as a log...
CREATE TABLE r.visited (
    uzer integer REFERENCES uzers(id) ON DELETE CASCADE ON UPDATE CASCADE,
    medium integer REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
    when timestamptz DEFAULT clock_timestamp() UNIQUE,
    visits integer DEFAULT 0,
    UNIQUE(uzer,medium)
);

CREATE TABLE r.describes (
    tag integer REFERENCES tags(id) ON DELETE CASCADE ON UPDATE CASCADE,
    medium integer REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE(tag,medium)
);

CREATE TABLE r.contains (
    medium integer REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
    thing INTEGER REFERENCES things(id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE(medium,thing)
);

CREATE TABLE species(
    id SERIAL PRIMARY KEY,
    ident TEXT UNIQUE,
    description TEXT);

CREATE TABLE r.species(
   species integer REFERENCES species(id)  ON DELETE CASCADE ON UPDATE CASCADE,
   medium integer REFERENCES media(id)  ON DELETE CASCADE ON UPDATE CASCADE,
   UNIQUE(species,medium));

CREATE TABLE r.performedin (
    act INTEGER REFERENCES acts(id) ON DELETE CASCADE ON UPDATE CASCADE,
    medium integer REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE(medium,act)
);

CREATE TABLE r.references (
    medium integer REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
    verse integer REFERENCES verses(id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE(medium,verse)
);

-- last categorized in, so we don't throw stuff back in general 'tags' all the time
CREATE TABLE r.categorized (
    name TEXT,
    category regclass, -- table name
    changed timestamptz DEFAULT now());

-- now some indexes... for any time we have one, and have to look up many, i.e. all concepts tagging 
-- an image, or all artists drawing an image, or all people in an image, or all images a person is in... or all images tagged by a concept... we have to just do all possible combos don't we

CREATE INDEX r.conceptsformedium ON r.describes(medium);
CREATE INDEX r.artistsformedium ON r.drew (medium);
CREATE INDEX r.peopleformedium ON r.portrays (medium);
CREATE INDEX r.actsformedium ON r.performedin(medium);
CREATE INDEX r.thingsformedium ON r.contains(medium);
CREATE INDEX r.versesformedium ON r.references(medium);

CREATE INDEX r.mediaforconcept ON r.describes(tag);
CREATE INDEX r.mediaforartist ON r.drew(artist);
CREATE INDEX r.mediaforpeople ON r.portrays(person);
CREATE INDEX r.mediaforacts ON r.performedin(act);
CREATE INDEX r.mediaforthings ON r.contains(thing);
CREATE INDEX r.mediaforverse ON r.references(verse);

-- and now... we go insane

CREATE TYPE derp1 AS (id INTEGER, name TEXT);
CREATE TYPE derp2 AS (id INTEGER, name TEXT, sexiness INTEGER);

SELECT 
array(SELECT ROW(tags.id,tags.name)::derp1
    FROM tags
        INNER JOIN r.describes ON tags.id = r.describes.tag
    WHERE r.describes.medium = media.id),
array(SELECT ROW(artists.id,people.name)::derp1
    FROM artists 
        INNER JOIN people ON people.id = artists.id 
        INNER JOIN r.drew ON r.drew.artist = artists.id 
    WHERE r.drew.medium = media.id),
array(SELECT ROW(people.id,people.name)::derp1
    FROM people
        INNER JOIN r.portrays ON people.id = r.portrays.person
    WHERE r.portrays.medium = media.id),
array(SELECT ROW(acts.id,acts.name,acts.sexiness)::derp2
    FROM acts
        INNER JOIN r.performedin ON acts.id = r.performedin.act
    WHERE r.performedin.medium = media.id),
array(SELECT ROW(things.id,things.ident)::derp1
    FROM things
        INNER JOIN r.contains ON things.id = r.contains.thing
    WHERE r.contains.medium = media.id),
array(SELECT ROW(verses.id,verses.name)::derp1
    FROM verses
        INNER JOIN r.references ON verses.id = r.references.verse
    WHERE r.references.medium = media.id)
FROM media WHERE media.id = $1;

"/~media/artist:freedomthai/character:apple bloom/species:horse/act:vaginal penetration/-act:rape/feral/"
->

SELECT id FROM media WHERE
   id IN (
-- artist:
    SELECT medium FROM r.drew WHERE 
    artist = (SELECT artists.id FROM artists INNER JOIN people ON people.id = artists.id WHERE
        people.name = 'freedomthai')
    INTERSECT
-- character:
    SELECT medium from r.portrays WHERE
    person = (SELECT people.id FROM people WHERE people.name = 'apple bloom')
    INTERSECT
-- derp (no special relation known):
    SELECT medium FROM r.describes WHERE
    tag = (SELECT tag.id FROM tags WHERE tag.name = 'derp:herp')
-- species 
    SELECT medium FROM r.species WHERE
    species = (SELECT id FROM species WHERE name = 'horse')
-- act:
    SELECT medium FROM r.performedin WHERE
    act = (SELECT acts.id FROM acts WHERE acts.name = 'vaginal penetration')
    EXCEPT
-- act:
    SELECT medium FROM r.performedin WHERE
    act = (SELECT acts.id FROM acts WHERE acts.name = 'rape')
    INTERSECT
-- general:
    SELECT medium FROM r.describes WHERE
    tag = (SELECT tags.id FROM tags WHERE tags.name = 'feral'));

inserting "artist:freedomthai, apple bloom, derp:herp, species:horse, horse, act:vaginal penetration, feral, nonexistenttag, artist:notreallyherp"
->

-- first check unqualified categories

SELECT category FROM categorized WHERE name = 'apple bloom';
-> "people"

SELECT category FROM categorized WHERE name = 'horse';
-> "species"
-> merge horse/species:horse

SELECT category FROM categorized WHERE name = 'feral';
-> no results

SELECT category FROM categorized WHERE name = 'nonexistenttag';
-> nada

-- then, get the numbers for the things

SELECT id FROM people WHERE name  = 'freedomthai';
-> 1234

SELECT id FROM artists WHERE id = 1234;
-> 1234

SELECT id FROM people WHERE name = 'apple bloom';
-> 1235

SELECT id FROM tags WHERE name  = 'derp:herp';
-> 1234

SELECT id FROM species WHERE name = 'horse';
-> 1234

SELECT id FROM act WHERE name = 'vaginal penetration';
-> 1234

SELECT id FROM tags WHERE name = 'feral';
-> 1235

SELECT id FROM tags WHERE name = 'nonexistenttag';
-> nada

INSERT INTO tags (name) VALUES ('nonexistenttag');
-> 1236

SELECT id FROM people WHERE name = 'notreallyherp';
-> nada

INSERT INTO people (name) VALUES ('notreallyherp');
-> 1236
INSERT INTO artists (id) VALUES (1235);

INSERT INTO medium (...) RETURNING id;
-> 1234

-- now we have
(artist, 1234),(people, 1235),(tags,1234),(species,1234),(act,1234),(tags,1235),(artist,1236)
-- for medium 1234

template := 'INSERT INTO r.%1$s (%2$s,%3$s) SELECT $1,$2 EXCEPT SELECT %2$s,%3$s FROM r.%1$s WHERE %2$s = $1 AND %3$s = $2';

EXECUTE format(template,'drew','artist','medium') USING 1234, 1234;
EXECUTE format(template,'portrays','person','medium') USING 1235, 1234;
EXECUTE format(template,'describes','tag','medium') USING 1234, 1234;
EXECUTE format(template,'performedin','act','medium') USING 1234, 1234;
EXECUTE format(template,'describes','tag','medium') USING 1235, 1234;
EXECUTE format(template,'drew','artist','medium') USING 1236, 1234;
