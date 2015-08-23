CREATE TABLE media (
    id INTEGER PRIMARY KEY,
    name TEXT,
    hash BLOB,
    created DATETIME,
    added DATETIME,
    size INTEGER,
    type TEXT,
    md5 BLOB,
    thumbnailed DATETIME,
--    sources integer[],
    modified DATETIME,
    derphash BLOB,
    phashfail NUMERIC DEFAULT FALSE,
    phash NUMERIC
);

CREATE TABLE sources (
  id INTEGER PRIMARY KEY,
  medium INTEGER REFERENCES media(id),
  -- 0 = http(s)://
  -- 1 = file://
  -- 2 = ftp://?
  -- 3 = freenet:??
  schema INTEGER DEFAULT 0,
  uri TEXT);

CREATE TABLE tags (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  complexity INTEGER DEFAULT 0 NOT NULL);

CREATE TABLE media_tags (
  id INTEGER PRIMARY KEY,
  medium INTEGER REFERENCES media(id) ON DELETE CASCADE NOT NULL,
  tag INTEGER REFERENCES media(id) ON DELETE CASCADE NOT NULL,
  unique(medium,tag));
