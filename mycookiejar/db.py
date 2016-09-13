db = None

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
