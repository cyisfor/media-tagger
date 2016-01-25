CREATE TABLE media (
    id INTEGER PRIMARY KEY,
    name TEXT,
    hash BLOB NOT NULL,
    created DATETIME NOT NULL,
    added DATETIME NOT NULL,
    size INTEGER NOT NULL,
    type TEXT NOT NULL,
    md5 BLOB NOT NULL,
    thumbnailed DATETIME NOT NULL,
--    sources integer[],
    modified DATETIME NOT NULL,
    derphash BLOB NOT NULL,
    phashfail NUMERIC DEFAULT FALSE NOT NULL,
    phash NUMERIC NOT NULL
);

CREATE TABLE sources (
  id INTEGER PRIMARY KEY,
  medium INTEGER REFERENCES media(id) ON DELETE CASCADE NOT NULL,
  -- 0 = http(s)://
  -- 1 = file://
  -- 2 = ftp://?
  -- 3 = freenet:??
  schema INTEGER DEFAULT 0 NOT NULL,
  uri TEXT);

CREATE TABLE tags (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  complexity INTEGER DEFAULT 0 NOT NULL);

CREATE TABLE media_tags (
  id INTEGER PRIMARY KEY,
  medium INTEGER REFERENCES media(id) ON DELETE CASCADE NOT NULL,
  tag INTEGER REFERENCES tags(id) ON DELETE CASCADE NOT NULL,
  unique(medium,tag));
