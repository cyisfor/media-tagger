from db import ProgrammingError
import db

db.setup(
    'CREATE TABLE hosts (id SERIAL PRIMARY KEY, host TEXT UNIQUE, resume TIMESTAMPTZ UNIQUE)',
    '''CREATE TABLE parseQueue (
    id SERIAL PRIMARY KEY, 
    added TIMESTAMPTZ DEFAULT now() NOT NULL, 
    tries integer default 0, 
    uri TEXT UNIQUE,done boolean default false,
    host INTEGER REFERENCES hosts(id))''')

def enqueue(uri):
    try: db.execute("INSERT INTO parseQueue (uri) VALUES ($1)",(uri,))
    except ProgrammingError as e:
        print("error",e.info)

def top():
    r = db.execute('''SELECT uri FROM parseQueue WHERE NOT done AND tries < 5 AND
    (host IS NULL OR EXISTS 
        (select id FROM hosts WHERE resume > clock_timestamp AND id = parseQueue.id))
    ORDER BY added DESC LIMIT 1''')
    if r: return r[0][0]
    return None

def host(uri):
    host = urllib.parse.urlsplit(uri).netloc
    colon = host.find(':')
    if colon > 0:
        return host[:colon]
    return host

def delay(host,interval='10 seconds'):
    r = db.execute('SELECT id FROM hosts WHERE host = $1',(host,))
    if r:
        host = r[0][0]
    else:
        host = db.execute('INSERT INTO hosts (host) VALUES ($1) RETURNING id',(host,))
    db.execute('UPDATE hosts SET resume = clock_timestamp() + $2 WHERE id = $1',(host,interval))

def fail(uri):
    print('failing for',repr(uri))
    db.execute("UPDATE parseQueue SET tries = tries + 1 WHERE uri = $1",(uri,))
def megafail(uri):
    db.execute("UPDATE parseQueue SET tries = 9001 WHERE uri = $1",(uri,))
def win(uri):
    db.execute("UPDATE parseQueue SET done = TRUE WHERE uri = $1",(uri,))
