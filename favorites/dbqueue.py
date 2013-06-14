from db import c,ProgrammingError

try: c.execute("CREATE TABLE parseQueue (id SERIAL PRIMARY KEY, added TIMESTAMPTZ DEFAULT now() NOT NULL, tries integer default 0, uri TEXT UNIQUE)")
except ProgrammingError: pass

def enqueue(uri):
    try: c.execute("INSERT INTO parseQueue (uri) VALUES ($1)",(uri,))
    except ProgrammingError as e:
        print("error",dir(e))
def top():
    r = c.execute("SELECT uri FROM parseQueue WHERE tries < 5 ORDER BY added DESC LIMIT 1")
    if r: return r[0][0]
    return None
def fail(uri):
    c.execute("UPDATE parseQueue SET tries = tries + 1 WHERE uri = $1",(uri,))
def win(uri):
    c.execute("DELETE FROM parseQueue WHERE uri = $1",(uri,))

