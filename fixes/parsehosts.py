import db
from favorites.dbqueue import host

from itertools import count

counter = count(1)

with db.transaction():
    for id,uri in db.execute('SELECT id,uri FROM parsequeue WHERE host IS NULL'):
        try: boast = host(uri)
        except ValueError: pass
        except:
            print(uri)
            raise
        print(boast,'=>',uri)
        db.execute('UPDATE parsequeue SET host = $2 WHERE id = $1',(id,boast))
        if next(counter) % 100 == 0:
            db.retransaction()
