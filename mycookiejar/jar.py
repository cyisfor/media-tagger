import time

try:
	import http.cookiejar as cookiejar
except ImportError:
	import cookielib as cookiejar

# set in setup.py
db = None
findDomain = None
findURL = None
cookieGetter = None
extra_fields = None

def splitdict(d):
	k = d.items()
	# preserve order of keys and values
	v = tuple(e[1] for e in k)
	k = tuple(e[0] for e in k)
	return k,v

def execute(stmt,args):
	print(stmt)
	print(args)
	return db.execute(stmt,args)

def update(domain,path,name,value,creationTime,**attrs):
	baseDomain = ".".join(name.rsplit(".",2)[-2:])
	values = [None]*len(extra_fields)
	for i,field in enumerate(extra_fields):
		values[i] = attrs[field]
	with db:
		url,created = findURL(findDomain(domain)[0],path)
		def doinsert():
			execute(
				"INSERT INTO cookies (lastAccessed,creationTime,name,url,value"
				+ "".join((','+f) for f in extra_fields) + ")"
				+ "VALUES (?1,?1,?2,?3,?4"
				+ "".join(",?"+str(i+4) for i in range(len(extra_fields)))
				+ ")",
				[time.time(),name,url,value] + values)
		if created:
			doinsert()
			return

		r = db.execute("SELECT id,creationTime FROM cookies WHERE url = ? AND name = ?", (url, name))
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
	def __str__(self):
		return "Jar<A sqlite cookie jar>"
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
	def set_cookie(self,cookie,creationTime):
		herderp = dict()
		for n in dir(cookie):
			if n.startswith('_'): continue
			v = getattr(cookie,n)
			if callable(v): continue
			herderp[n] = v
		update(creationTime=creationTime,
					 **herderp)
