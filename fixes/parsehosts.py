import db
from favorites.dbqueue import host

with db.transaction():
    for id,uri in db.execute('SELECT id,uri FROM parsequeue WHERE host IS NULL'):
        boast = host(uri)
        print(boast,'=>',uri)
        r = db.execute('SELECT id FROM hosts WHERE host = $1',(boast,))
        if not r:
            r = db.execute('INSERT INTO hosts (host) VALUES ($1) RETURNING id',(boast,))
        db.execute('UPDATE parsequeue SET host = $2 WHERE id = $1',(id,r))
