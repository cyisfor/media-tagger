-- mostly ganked from mozilla's cookes sqlite file, but with more better stuff
CREATE TABLE IF NOT EXISTS urls (
 id INTEGER PRIMARY KEY,
 host TEXT NOT NULL,
 baseDomain TEXT NOT NULL,
 path TEXT NOT NULL,
 UNIQUE(baseDomain,path));
 
CREATE TABLE IF NOT EXISTS cookies (
 id INTEGER PRIMARY KEY,
 path INTEGER NOT NULL REFERENCES urls(id),
 name TEXT NOT NULL,
 value TEXT NOT NULL,
 expires INTEGER NOT NULL, -- must be in seconds for the header
 lastAccessed REAL NOT NULL,
 creationTime REAL NOT NULL,
 isSecure BOOLEAN NOT NULL,
 isHttpOnly BOOLEAN NOT NULL,
 CONSTRAINT uniqueid UNIQUE (name,path));

CREATE INDEX basedomain ON urls (baseDomain);
