from db import c,ProgrammingError

try: c.execute("CREATE TABLE parseQueue (id SERIAL PRIMARY KEY, added TIMESTAMPTZ DEFAULT now() NOT NULL, uri TEXT UNIQUE)")
except ProgrammingError: pass

def enqueue(uri):
    try: c.execute("INSERT INTO parseQueue (uri) VALUES ($1)",(uri,))
    except ProgrammingError: pass
def top():
    r = c.execute("SELECT uri FROM parseQueue ORDER BY added DESC LIMIT 1")
    if r: return r[0][0]
    return None
def dequeue(uri):
    c.execute("DELETE FROM parseQueue WHERE uri = $1",(uri,))

