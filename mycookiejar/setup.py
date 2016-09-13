from .db import execute

import sqlite3
from orm import create_table,column,references,make_selins

class Tables:
	domains = create_table(
		"domains",
		column("domain","TEXT","UNIQUE"))
	urls = create_table(
		"urls",
		column("domain",references("domains")),
		column("path","TEXT"))
	cookies = create_table(
		"cookies",
		column("url",references("urls")),
		column("name","TEXT"),
		column("value","TEXT"),
		column("expires","REAL"),
		column("port","INTEGER",notNull=False),
		column("port_specified","BOOLEAN"),
		column("lastAccessed","REAL"),
		column("creationTime","REAL"),
		column("secure","BOOLEAN"))
	info = create_table(
		"info",
		column("singleton","BOOLEAN","UNIQUE","DEFAULT TRUE"),
		column("lastChecked","REAL"))

try:
	execute("SELECT id FROM cookies LIMIT 1")
except sqlite3.OperationalError:
	importing = True
else:
	importing = False
	execute(Tables.domains)
	execute(Tables.urls)
	execute(Tables.cookies)
	execute(Tables.info)
	execute("CREATE INDEX IF NOT EXISTS byexpires ON cookies(expires)")
	execute("CREATE UNIQUE INDEX IF NOT EXISTS unique_urls ON urls(domain,path)")
	execute("CREATE UNIQUE INDEX IF NOT EXISTS unique_cookies ON cookies(name,url)")
	execute("CREATE UNIQUE INDEX IF NOT EXISTS one_info ON info(singleton)")
	import time
	execute("INSERT INTO info (lastChecked) VALUES (?)",(time.time(),))

info = execute("SELECT lastChecked FROM info").fetchone()
assert(info)
lastChecked = info[0]
def checked():
	execute("UPDATE info SET lastChecked = ?",(time.time(),))

selins = make_selins(execute)
	
def memoize(f):
	from functools import lru_cache
	f = lru_cache()(f)
	# sigh
	def wrapper(*a,**kw):
		hits = f.cache_info().hits
		ret,created = f(*a,**kw)
		if created:
			if hits != f.cache_info().hits:
				created = False
		return ret, created
	return wrapper

findDomain = memoize(selins("domains","domain")())
findURL = memoize(selins("urls","domain","path")())

extra_fields = tuple(
	set(c.name for c in Tables.cookies.columns)
	-
	{'url', 'name','value', 'lastAccessed', 'creationTime'})

def updoot(off):
	return ("UPDATE cookies SET "
			+ ",".join(n+" = ?"+str(i+off) for i,n in enumerate(extra_fields))
			+ ", lastAccessed = ?1")
update_id_stmt = updoot(3) + "\n WHERE id = ?2"


policy = None
