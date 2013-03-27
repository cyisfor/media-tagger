CREATE TABLE things(id BIGSERIAL PRIMARY KEY, 
    neighbors bigint[]);
CREATE TABLE media(id bigint PRIMARY KEY REFERENCES things(id) 
    ON DELETE CASCADE ON UPDATE CASCADE,
    name TEXT,
    hash character(28) UNIQUE,
    created timestamp with time zone,
    added timestamp with time zone UNIQUE DEFAULT NOW(),
    size integer,
    type text,
    md5 character(32),
    thumbnailed timestamp with time zone,
    sources int[]);
CREATE TABLE images(id bigint PRIMARY KEY REFERENCES media(id) 
    ON DELETE CASCADE ON UPDATE CASCADE,
    animated boolean,
    width integer,
    height integer,
    ratio real);
CREATE TABLE sources(id SERIAL PRIMARY KEY,
    checked timestamp with time zone DEFAULT NOW());
CREATE TABLE urisources(id INTEGER PRIMARY KEY REFERENCES sources(id) 
    ON DELETE CASCADE ON UPDATE CASCADE,
            uri text not null UNIQUE,
            code integer);
CREATE TABLE filesources(id INTEGER PRIMARY KEY REFERENCES sources(id) 
    ON DELETE CASCADE ON UPDATE CASCADE,
    path text UNIQUE);
CREATE TABLE tags(id bigint PRIMARY KEY REFERENCES things(id) 
    ON DELETE CASCADE ON UPDATE CASCADE,
    name TEXT UNIQUE);

CREATE INDEX tagsearch ON things USING gin(neighbors);
\echo 'Gin!'
CREATE INDEX bytype ON media(type);
CREATE INDEX bypath ON filesources(path);
CREATE INDEX byuri ON urisources(uri);
CREATE INDEX mostrecent ON media(added);
CREATE INDEX oldest ON media(created);
CREATE UNIQUE INDEX whenchecked ON sources(checked);
\echo 'Other indices'
