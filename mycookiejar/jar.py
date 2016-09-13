import time

try:
	import http.cookiejar as cookiejar
except ImportError:
	import cookielib as cookiejar

from .db import db,execute
assert(db,"please setup before using this!")

from .setup import extra_fields,findDomain,findURL,extra_fields,update_id_stmt,importing,policy

def splitdict(d):
	k = d.items()
	# preserve order of keys and values
	v = tuple(e[1] for e in k)
	k = tuple(e[0] for e in k)
	return k,v

def now(*a):
	return time.time()

def update(domain,path,name,value,creationTime,**attrs):
	baseDomain = ".".join(name.rsplit(".",2)[-2:])
	values = [None]*len(extra_fields)
	for i,field in enumerate(extra_fields):
		values[i] = attrs[field]
	with db:
		url,created = findURL(findDomain(domain)[0],path)
		def doinsert():
			execute(
				"INSERT INTO cookies (name,value,url,lastAccessed,creationTime"
				+ "".join((','+f) for f in extra_fields) + ")"
				+ "VALUES (?,?,?,?,?"
				+ "".join((",?",) * len(extra_fields))
				+ ")",
				[name,value,url,now(),creationTime] + values)
		if created:
			import sqlite3
			try:
				doinsert()
			except sqlite3.IntegrityError:
				print(name,url)
				raise
			# have to commit here, because selecting won't return the new rows
			db.__exit__(None,None,None)
			db.__enter__()
			return

		r = execute("SELECT id,creationTime FROM cookies WHERE url = ? AND name = ?", (url, name))
		r = r.fetchone()
		if not r:
			doinsert()
			return
		ident,oldcreation = r
		if oldcreation <= creationTime:
			return
		r = execute(update_id_stmt,
			[creationTime,ident] + values)
		if r.rowcount == 0:
			# it got deleted?
			doinsert()

class Cookie:
	version = 0
	fields = ['name','value','secure','expires',
	          'port','port_specified']
	def __init__(self, domain, path, r):
		self.domain = domain
		self.path = path
		for i,field in enumerate(self.fields):
			setattr(self,field,r[i])
	def is_expired(self,now):
		return self.expires < now
	
class Jar(cookiejar.CookieJar):
	def __init__(self, policy=None):
		super().__init__(policy)
		del self._cookies # just to keep us honest
	def __enter__(self):
		if verbose:
			print('starting transaction')
		return db.__enter__()
	def __exit__(self,*a):
		if verbose:
			print('committing')
		return db.__exit__(*a)
	def __str__(self):
		return "Jar<A sqlite cookie jar>"
	def _cookies_for_domain(self, domain, baseDomain, request):
		for urlid,path in execute(
				"SELECT id,path FROM urls WHERE domain = ?1",
				(baseDomain,)):
			if not self._policy.path_return_ok(path, request): continue
			for cookie in execute("SELECT "+",".join(Cookie.fields)
			                      +" FROM cookies WHERE url = ?",
															 (urlid,)):
				cookie = Cookie(domain,path,cookie)
				if not self._policy.return_ok(cookie, request): continue
				yield cookie
	def __cookies_for_request(self, request):
		for baseDomain,domain in execute("SELECT id,domain FROM domains"):
			if not self._policy.domain_return_ok(domain, request): continue
			yield from self._cookies_for_domain(domain, baseDomain,request)
	def _cookies_for_request(self, request):
		# this MUST return a mutable list
		return list(self.__cookies_for_request(request))
	def clear_expired_cookies(self, request = None):
		urls = "SELECT url FROM cookies WHERE expires < ?"
		domains = "SELECT domain FROM urls WHERE id IN (" + urls + ")"
		currentTime = now()
		with db:
			r = execute("DELETE FROM cookies WHERE expires < ?",
			            (currentTime,))
			if r.rowcount > 0:
				print("expired",r.rowcount,"cookies")
				#time.sleep(1)
			execute("DELETE FROM urls WHERE id IN (" + urls + ")",
			(currentTime,))
			execute("DELETE FROM domains WHERE id IN (" + domains + ")",
			(currentTime,))
	def set_cookie(self,fields,creationTime):
		herderp = dict()
		for n in dir(cookie):
			if n.startswith('_'): continue
			v = getattr(cookie,n)
			if callable(v): continue
			herderp[n] = v
		update(creationTime=creationTime,
					 **herderp)

Jar.now = now

import sys
jar = Jar(policy)
sys.modules[__name__] = jar
import mycookiejar
mycookiejar.jar = jar
