-- mostly ganked from mozilla's cookes sqlite file, but with more better stuff
CREATE TABLE IF NOT EXISTS cookies (
 id INTEGER PRIMARY KEY,
 baseDomain TEXT NOT NULL,
 name TEXT NOT NULL,
 value TEXT NOT NULL,
 host TEXT NOT NULL,
 path TEXT NOT NULL,
 expires INTEGER NOT NULL, -- must be in seconds for the header
 lastAccessed REAL NOT NULL,
 creationTime REAL NOT NULL,
 isSecure BOOLEAN NOT NULL,
 isHttpOnly BOOLEAN NOT NULL,
 CONSTRAINT uniqueid UNIQUE (name,
 host,
 path));

CREATE INDEX basedomain ON cookies (baseDomain);
