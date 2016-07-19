import time
start = time.time()
from filedb import top
from contextlib import closing,contextmanager

import io

import gzip,zlib
import sys
import os,tempfile
try:
	import urllib.request as urllib
	import urllib.parse as urlparse
	import urllib.error as urlerror
except ImportError:
	import urllib2 as urllib
	urlerror = urllib
	import urlparse	
Request = urllib.Request

try:
	import http.client as http
except ImportError:
	import httplib as http

import shutil
import glob
import re

from six import raise_from
from mysix import textreader

print('bou',time.time()-start)
sys.stdout.flush()
oj = os.path.join

proxy = urllib.ProxyHandler({"http": "http://127.0.0.1:8123"})
handlers = [proxy]

space = re.compile('[ \t]+')

if not 'skipcookies' in os.environ:
	# this can take a while...

	try:
		import http.cookiejar as cookiejar
	except ImportError:
		import cookielib as cookiejar
		
	jar = cookiejar.CookieJar()
	handlers.append(urllib.HTTPCookieProcessor(jar))
	fields = 'version, name, value, port, port_specified, domain, domain_specified, domain_initial_dot, path, path_specified, secure, expires, discard, comment, comment_url, rfc2109'.split(',')
	fields = [f.strip() for f in fields]
	def typefield():
		for f in fields:
			if f in {'port_specified',
					 'domain_specified',
					 'domain_initial_dot',
					 'path_specified',
					 'discard'}:
				yield f + ' BOOLEAN';
			else:
				yield f + ' TEXT';

	import sqlite3
	import json
				
	with closing(sqlite3.connect(oj(top,"temp","cookies.sqlite"))) as db:
		db.execute('CREATE TABLE IF NOT EXISTS cookies ('+',\n'.join(typefield())+'\n)')
		with closing(db.cursor()) as c:
			c.execute('SELECT '+','.join(fields)+' FROM cookies');
			for row in c:
				jar.set_cookie(cookiejar.Cookie(*row))
			for cookie in jar:
				c.execute('INSERT INTO cookies ('+','.join(fields)+') VALUES ('+
						   ','.join('?' for f in fields) + ')',
						  tuple(getattr(cookie,f) for f in fields))	
		
	def fileProcessor(f):
		def wrapper(path):
			print('getting',path)
			if not os.path.exists(path): return
			for c in f(path):
				jar.set_cookie(c)
		return wrapper

	def lineProcessor(f):
		@fileProcessor
		def wrapper(path):
			with textreader(open(path,'rb')) as inp:
				for line in inp:
					c = f(line)
					if c:
						yield c
		return wrapper

	@fileProcessor
	def get_cookies(ff_cookies):
		with closing(sqlite3.connect(ff_cookies)) as con:
			cur = con.cursor()
			cur.execute("SELECT host, path, isSecure, expiry, name, value FROM moz_cookies")
			for item in cur.fetchall():
				yield cookiejar.Cookie(0, item[4], item[5],
					None, False,
					item[0], item[0].startswith('.'), item[0].startswith('.'),
					item[1], False,
					item[2],
					item[3], item[3]=="",
					None, None, {})
	@lineProcessor
	def get_text_cookies(line):
		host, isSession, path, isSecure, expiry, name, value = space.split(line,6)
		return cookiejar.Cookie(
			0, name, value,
			None, False,
			host, host.startswith('.'), host.startswith('.'),
			path, False,
			isSecure=='TRUE',
			int(expiry), expiry=="",
			None, None, {})
	@lineProcessor
	def get_json_cookies(line):
		try:
			c = json.loads(line)
			host = c['host']
		except KeyError:
			return
		return cookiejar.Cookie(
			0, c['name'], c['value'],
			None, False,
			host, host.startswith('.'), host.startswith('.'),
			c['path'],not not c['path'],
			c['isSecure'], c['expires'],not not c['expires'],
			None, None, {})
	
	get_cookies(oj(top,"cookies.sqlite"))
	
	#for ff in glob.glob(os.path.expanduser("~/.mozilla/firefox/*/")):
	ff = os.path.expanduser("~/.mozilla/firefox/aoeu.default")
	get_cookies(oj(ff,'cookies.sqlite'))
	get_json_cookies(oj(ff,'cookies.jsons'))

	get_text_cookies("/extra/user/tmp/cookies.txt")	
	get_json_cookies("/extra/user/tmp/cookies.jsons")

	with closing(sqlite3.connect(oj(top,"temp","cookies.sqlite"))) as db:
		for cookie in jar:
			stmt = 'INSERT INTO cookies ('+','.join(fields)+') VALUES ('+ ','.join('?' for f in fields)+')'
			args = tuple(getattr(cookie,f) for f in fields)
			#print(stmt,tuple(enumerate(args)))
			db.execute(stmt,args)
					   

class HeaderWatcher(urllib.HTTPHandler):
	class Client(http.HTTPConnection):
		def request(self,method,selector,data,headers):
			print('sending headers',headers)
			super().request(method,selector,data,headers)
	def http_open(self, req):
		return self.do_open(self.Client, req)

handlers.append(HeaderWatcher())

opener = urllib.build_opener(*handlers)
opener.addheaders = [
		('User-agent','Mozilla/5.0 (X11; Linux x86_64; rv:19.0) Gecko/20100101 Firefox/19.0'),
		('Accept-Encoding', 'gzip,deflate')]
urllib.install_opener(opener)

class URLError(Exception): 
	def __str__(self):
		return str(self.__cause__) + ': ' + str(self.args[0])

@contextmanager
def myopen(request):
	if not isinstance(request,Request):
		request = Request(request)
	try:
		request.full_url.encode('ascii')
	except UnicodeEncodeError as e:
		url = list(urlparse.urlparse(request.full_url))
		for i in range(2,len(url)):
			url[i] = urlparse.quote(url[i],safe="/&=?+")
		request.full_url = urlparse.urlunparse(url)
	print('requesting',request.full_url)
	try:
		with closing(opener.open(request)) as inp:
			headers = inp.headers
			encoding = headers['Content-Encoding']
			if encoding == 'gzip':
				inp = gzip.GzipFile(fileobj=inp,mode='rb')
			elif encoding == 'deflate':
				data = inp.read(0x40000)
				try: data = zlib.decompress(data)
				except zlib.error:
					data = zlib.decompress(data,-zlib.MAX_WBITS)
				inp = io.StringIO(data)
			inp.headers = headers
			yield inp
	except urlerror.HTTPError as e:
		if e.code == 503:
			print('head',e.headers)
			print(e.read())
		raise
	except urlerror.URLError as e:
		raise_from(URLError(request.full_url),e)

	# if isinstance(dest,str):
	#	 try: stat = os.stat(dest)
	#	 except OSError: pass
	#	 else:
	#		 if not isinstance(request,Request):
	#			 request = Request(request)
	#		 request.add_header('If-Modified-Since',email.utils.formatdate(stat.st_mtime))

progress = None
	
def myretrieve(request,dest):
	global derps
	with myopen(request) as inp:
		headers = inp.headers
		total = headers.get('Content-Length')
		block = bytearray(0x1000)
		sofar = 0
		print('progress?',progress)
		while True:
			amt = inp.readinto(block)
			if amt == 0: break
			dest.write(memoryview(block)[:amt])
			if derps:
				sofar += amt
				if progress:
					progress(sofar,total)
		return inp.headers

print('urllib has been setup for proxying')
