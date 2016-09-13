from db import db

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
	execute("CREATE UNIQUE INDEX IF NOT EXISTS info ON info(singleton)")
	execute("INSERT INTO info (lastChecked) VALUES (?)",(time.time(),))

info = db.execute("SELECT lastChecked FROM info").fetchone()
assert(info)
lastChecked = info[0]
def checked():
	db.execute("UPDATE info SET lastChecked = ?",(time.time(),))
