import os,sys
oj = os.path.join

from orm import create_table,column,references,make_selins

class Tables:
	domains = create_table(
		"domains",
		column("domain","TEXT","UNIQUE"))
	urls = create_table(
		"urls",
		column("domain",references("domains")),
		column("path","TEXT"),
		"UNIQUE(domain,path)")
	cookies = create_table(
		"cookies",
		column("url",references("urls")),
		column("name","TEXT"),
		column("value","TEXT"),
		column("port","INTEGER","DEFAULT 0"),
		column("port_specified","BOOLEAN"),
		column("lastAccessed","REAL"),
		column("creationTime","REAL"),
		column("secure","BOOLEAN"))

def setup(place,name="cookies.sqlite",policy=None):
	from mycookiejar import jar
	import sqlite3
	jar.db = sqlite3.connect(oj(place,name))
	jar.db.execute(Tables.domains)
	jar.db.execute(Tables.urls)
	jar.db.execute(Tables.cookies)
	selins = make_selins(jar.db)

	jar.findDomain = selins("domains","domain")()
	jar.findURL = selins("urls","domain","path")()
	jar.cookieGetter = selins("cookies","url","name") # don't commit insert
	jar.extra_fields = tuple(
		set(c.name for c in Tables.cookies.columns)
		-
		{'url', 'name','value', 'lastAccessed', 'creationTime'})

	def updoot(off):
		return ("UPDATE cookies SET "
				+ ",".join(n+" = ?"+str(i+off) for i,n in enumerate(jar.extra_fields))
				+ ", lastAccessed = ?1")
	jar.update_stmt = updoot(4) + "\n WHERE url = ?2 AND name = ?3"
	jar.update_id_stmt = updoot(3) + "\n WHERE id = ?2"

	
	name= jar.__name__
	jar = jar.Jar(policy)
	sys.modules[name] = jar
	import mycookiejar
	mycookiejar.jar = jar
	# let's not do this a second time, thx
	def pythonsucks(*a):
		raise RuntimeError("don't setup twice!")
	sys.modules[__name__] = pythonsucks

import sys
sys.modules[__name__] = setup
