import os,sys,time
oj = os.path.join

try:
	import http.cookiejar as cookiejar
except ImportError:
	import cookielib as cookiejar


from orm import CreateTable,Column

class Tables:
	domains = CreateTable(
		"domains",
		Column("domain","TEXT","UNIQUE"))
	urls = CreateTable(
		"urls",
		Column("domain",References("domains")),
		Column("path","TEXT"),
		"UNIQUE(domain,path)")
	cookies = CreateTable(
		"cookies",
		Column("url",References("urls")),
		Column("name","TEXT"),
		Column("value","TEXT"),
		Column("port","INTEGER","DEFAULT 0"),
		Column("port_specified","BOOLEAN"),
		Column("secure","BOOLEAN"))

db = None
def setup(place,name="cookies.sqlite"):
	global db
	db = sqlite3.connect(oj(place,name))

def selins(name,*uniques):
	def provide_inserter(inserter=None):
		def get(self,*uniquevals):
			id = db.execute(
				"SELECT id FROM "+name+" WHERE "
				+ " AND ".join(val + " = ?" for val in uniques)
				uniquevals)
			if id:
				return id[0][0]
			if inserter:
				inserts = inserter().items()
				values = uniquevals + tuple(i[1] for i in inserts)
				keys = uniques + tuple(i[0] for i in inserts)
			else:
				# no extra columns to insert
				values = uniquevals
				keys = uniques
			db.execute("INSERT INTO "+name+" (" + ",".join(keys)
				           + ") VALUES (" + ",".join(("?",) * len(keys))
				           + ")",
				           values)
			return db.lastrowid
		return get
	return provide_inserter

findDomain = selins("domains","domain")()
findURL = selins("urls","domain","path")()
cookieGetter = selins("cookies","url","name") # don't commit insert

def getCookie(url,name,value,etc):
	@cookieGetter
	def _():
		return {'value': value, 'etc': etc}

def update(self,**values):
	baseDomain = ".".join(name.rsplit(".",2)[-2:])
	values = tuple((values[infields.get(n,n)] for n in fields))
	with db:
		r = db.execute(
			"UPDATE cookies SET "
			+ ",".join(n+" = ?"+str(i+6) for i,n in enumerate(fields))
			+ """, baseDomain = ?1,
			lastAccessed = ?2
			WHERE name = ?3 AND host = ?4 AND path = ?5""",
			(baseDomain, time.time()) + values)
		if r.rowcount == 0:
			db.execute(
				"INSERT INTO cookies (lastAccessed,createdTime"
				+ ",".join(fields) + ")"
				+ "VALUES (?1,?1,"
				+ ",".join("?"+str(i+2) for i in range(len(fields)))
				+ ")",
				(time.time(),) + values)
def cookies_for_request(self,urlid,**values):
	extra_names = tuple(values.keys())
	extra_values = tuple(values[n] for n in extra_names)
	return db.execute(
		"SELECT id FROM cookies WHERE path = ?1"
		+"".join(" AND " + name + " = ?"+str(i+2) for i,name in enumerate(extra_names)),
		(urlid)+extra_values)

class Cookie(int): pass

class Jar(cookiejar.CookieJar):
	def __init__(self, args):
		"docstring"

	def _cookies_for_domain(self, baseDomain, request):
		for urlid,path in db.execute(
				"SELECT id,path FROM urls WHERE baseDomain = ?1",
				baseDomain):
			if not self._policy.path_return_ok(path, request): continue
			for cookie in db.execute("SELECT id FROM cookies WHERE path = ?",
															 (urlid,)):
				if not self._policy.return_ok(cookie, request): continue
				yield Cookie(cookie)
	def __cookies_for_request(self, request):
		for baseDomain,domain in db.execute("SELECT id,domain FROM domains"):
			if not self._policy.domain_return_ok(domain, request): continue
			yield from self._cookies_for_domain(baseDomain,request)
	def _cookies_for_request(self, request):
		# this MUST return a forward range
		return tuple(self.__cookies_for_request(request))

	def set_cookie(self,cookie):
		update(name=cookie.name,
					 value=cookie.value,
					 port=cookie.port,
					 **cookie)

return Jar()
