import os,sys,time
oj = os.path.join

try:
	import http.cookiejar as cookiejar
except ImportError:
	import cookielib as cookiejar

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
		column("secure","BOOLEAN"))

db = None
selins = None
def setup(place,name="cookies.sqlite"):
	global db,selins,findDomain,findURL,cookieGetter
	import sqlite3
	db = sqlite3.connect(oj(place,name))
	db.execute(Tables.domains)
	db.execute(Tables.urls)
	db.execute(Tables.cookies)
	selins = make_selins(db)

	findDomain = selins("domains","domain")()
	findURL = selins("urls","domain","path")()
	cookieGetter = selins("cookies","url","name") # don't commit insert

def getCookie(url,name,value,etc):
	@cookieGetter
	def _():
		return {'value': value, 'etc': etc}

def splitdict(d):
	k = d.items()
	# preserve order of keys and values
	v = tuple(e[1] for e in k)
	k = tuple(e[0] for e in k)
	return k,v

def update(domain,path,name,value,creationTime,**attrs):
	baseDomain = ".".join(name.rsplit(".",2)[-2:])
	attrs['value'] = value
	attrs = splitdict(attrs)
	with db:
		url,created = findURL(findDomain(domain),path)
		def doinsert():
			db.execute(
				"INSERT INTO cookies (lastAccessed,createdTime,name,url"
				+ ",".join(attrs[0]) + ")"
				+ "VALUES (?1,?1,?2,?3"
				+ ",".join("?"+str(i+4) for i in range(len(attrs[0])))
				+ ")",
				(time.time(),name,url) + attrs[1])
		if created:
			doinsert()
			return
		
		r = db.execute("SELECT id,creationTime FROM cookies WHERE url = ? AND name = ?")
		if r:
			ident,oldcreation = r[0]
			if oldcreation < creationTime:
				return
		r = db.execute(
			"UPDATE cookies SET "
			+ ",".join(n+" = ?"+str(i+3) for i,n in enumerate(attrs[0]))
			+ """, lastAccessed = ?1
			WHERE id = ?2""",
			(time.time(),ident) + attrs[1])
		if r.rowcount == 0:
			# it got deleted?
			doinsert()

def cookies_for_request(self,urlid,**values):
	extra_names = tuple(values.keys())
	extra_values = tuple(values[n] for n in extra_names)
	return db.execute(
		"SELECT id FROM cookies WHERE path = ?1"
		+"".join(" AND " + name + " = ?"+str(i+2) for i,name in enumerate(extra_names)),
		(urlid)+extra_values)

class Jar(cookiejar.CookieJar):
	def __init__(self, policy=None):
		super().__init__(policy)
		del self._cookies # just to keep us honest

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
	def set_cookie(self,cookie,creationTime=None):
		if creationTime is None:
			creationTime = self.creationTime
		herderp = dict()
		for n in dir(cookie):
			v = getattr(cookie,n)
			herderp[n] = v
		update(creationTime=creationTime,
					 **herderp)

