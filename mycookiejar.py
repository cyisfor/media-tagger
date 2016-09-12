import os,sys,time
oj = os.path.join

try:
	import http.cookiejar as cookiejar
except ImportError:
	import cookielib as cookiejar

def make(place,name="cookies.sqlite"):
	db = sqlite3.connect(oj(place,name))
	fields = ['name','value','host','path',
	          'expires','isSecure','isHttpOnly']:
	def update(self,**values):
		baseDomain = ".".join(name.rsplit(".",2)[-2:])
		values = tuple((values[n] for n in fields))
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

	class Jar(cookiejar.CookieJar):
		def _cookies_for_domain(self, baseDomain, request):
			for urlid,path in db.execute(
					"SELECT id,path FROM urls WHERE baseDomain = ?1",
					baseDomain):
				if not self._policy.path_return_ok(path, request): continue
				for cookie in db.execute("SELECT id FROM cookies WHERE path = ?",
				                         (urlid,)):
					if not self._policy.return_ok(cookie, request): continue
					yield cookie

	return Jar()
