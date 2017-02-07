from db import ProgrammingError
import db

import urllib.parse

db.setup(
	'CREATE TABLE hosts (id SERIAL PRIMARY KEY, host TEXT UNIQUE, resume TIMESTAMPTZ UNIQUE)',
	'''CREATE TABLE parseQueue (
	id SERIAL PRIMARY KEY,
	medium INTEGER REFERENCES media(id),
	added TIMESTAMPTZ DEFAULT now() NOT NULL, 
	tries integer default 0, 
	uri TEXT UNIQUE,
	host INTEGER REFERENCES hosts(id))''')

def host(uri):
	host = urllib.parse.urlsplit(uri).netloc
	colon = host.rfind(':')
	if colon > 0:
		host = host[:colon]
	r = db.execute('SELECT id FROM hosts WHERE host = $1',(host,))
	if r:
		host = r[0][0]
	else:
		host = db.execute('INSERT INTO hosts (host) VALUES ($1) RETURNING id',(host,))[0][0]
	return host

def enqueue(uri):
	if len(uri) > 2712: return
	try: h = host(uri)
	except ValueError: return
	res = db.execute("SELECT id FROM parseQueue WHERE uri = $1",(uri,))
	if res: return res[0][0]
	res = db.execute("INSERT INTO parseQueue (host,uri) SELECT $1,$2 WHERE NOT EXISTS (SELECT id FROM parseQueue WHERE uri = $2) RETURNING id",(h,uri))
	if not res: res = db.execute("SELECT id FROM parseQueue WHERE uri = $1",(uri,))
	
	return res[0][0]

criteria = '''medium IS NULL AND tries < 5 AND
	(host IS NULL OR EXISTS 
		(select id FROM hosts WHERE resume IS NULL OR resume > clock_timestamp() AND id = parseQueue.id))
'''

def remaining():
	return db.execute("SELECT count(1) from parseQueue WHERE "+criteria)[0][0]
	
def top():
	r = db.execute('SELECT id,uri FROM parseQueue WHERE ' + criteria +
				   'ORDER BY added DESC LIMIT 1')
	if r: return r[0]
	return None
def delay(host,interval='10 seconds'):
	db.execute('UPDATE hosts SET resume = clock_timestamp() + $2 WHERE id = $1',(host,interval))

def fail(uri):
	print('failing for',repr(uri))
	r = db.execute("UPDATE parseQueue SET tries = tries + 1 WHERE uri = $1",(uri,))
def megafail(uri):
	db.execute("UPDATE parseQueue SET tries = 9001 WHERE uri = $1",(uri,))
def win(medium,uri):
	db.execute("UPDATE parseQueue SET medium = $2 WHERE uri = $1",(uri,medium))
