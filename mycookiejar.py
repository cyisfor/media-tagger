import os,sys
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
				+ ",".join(n+" = ?"+str(i+5) for i,n in enumerate(fields))
				+ """, baseDomain = ?1,
				lastAccessed = ?2
				WHERE name = ?3 AND host = ?4 AND path = ?5""",
				(baseDomain, time.time(),) + values)
			if r.rowcount == 0:
				db.execute(
					"INSERT INTO cookies (lastAccessed,createdTime"
					+ ",".join(fields) + ")"
					+ "VALUES (?1,?1,"
					+ ",".join("?"+str(i) for i in range(len(fields)))
					+ ")",
					(time.time(),) + values)
	def get(self,name,host,path,isSecure)
	return update
