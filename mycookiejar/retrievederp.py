from mycookiejar.db import db
from mycookiejar import jar
import os,json
from contextlib import closing

def move(item,dest,src):
	v = item[src]
	del item[src]
	item[dest] = v
	return v

def fileProcessor(f):
	def wrapper(path):
		if not os.path.exists(path): return
		print('getting',path)
		with jar:
			for fields in f(path):
				jar.set_cookie(fields)
	return wrapper

def lineProcessor(f):
	@fileProcessor
	def wrapper(path):
		with open(path,'rb') as inp:
			creationTime = os.stat(inp.fileno()).st_mtime
			inp = textreader(inp)
			cookies = []
			for line in inp:
				c = f(line)
				if c:
					cookies.append(c)
			cookies.sort(key=lambda cookie:
								 (cookie['domain'],cookie['path'],cookie['name']))
			for c in cookies:
				yield c
	return wrapper

def regular_dict(cursor,row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d

@fileProcessor
def sqlite(ff_cookies):
	import sqlite3
	with closing(sqlite3.connect(ff_cookies)) as con:
		con.row_factory = regular_dict
		cur = con.cursor()
		# remember mozilla stores creationTime in microseconds
		cur.execute("""SELECT
		host AS domain,
		path,
		isSecure AS secure,
		expiry AS expires,
		name, value,
		creationTime / 1000000.0 AS creationTime
		FROM moz_cookies ORDER BY domain, path, name""")
		for item in cur.fetchall():
			if item['expires'] < jar.now():
				continue
			startdot = item['domain'].startswith('.')
			item['domain_specified'] = startdot # XXX: is this true?
			item['domain_initial_dot'] = startdot
			print(item)
			yield item

@lineProcessor
def text(line):
	fields = ('domain', 'isSession', 'path', 'secure',
	          'expires', 'name', 'value')
	values = space.split(line,len(fields)-1)
	expiry = values[5]
	item = dict(zip(fields,values))
	if expiry:
		expiry = float(expiry)
		if expiry < jar.now():
			return
		item['expiry'] = expiry
	else:
		item['expiry'] = None
	item['secure'] = item['secure'] == 'TRUE'
	startdot = item['domain'].startswith('.')
	item['domain_specified'] = startdot
	item['domain_initial_dot'] = startdot
	return item

@lineProcessor
def json(line):
	try:
		item = json.loads(line)
		domain = move(item,'domain','host')
	except KeyError:
		return
	if item['expires'] < jar.now():
		return
	move(item,'secure','isSecure')
	startdot = domain.startswith('.')
	item['domain_specified'] = startdot
	item['domain_initial_dot'] = startdot
	return item
