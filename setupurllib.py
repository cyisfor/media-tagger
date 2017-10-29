import time
start = time.time()
import note
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

print('bou',time.time()-start)
sys.stdout.flush()
oj = os.path.join
eu = os.path.expanduser

# how has this been working... at all?
#proxy = urllib.ProxyHandler({"http": "http://127.0.0.1:8123"})
#handlers = [proxy]
handlers = []

space = re.compile('[ \t]+')

if not 'skipcookies' in os.environ:
	# this can take a while...
	import mycookiejar
	from http.cookiejar import Cookie
	mycookiejar.setup(oj(top,"temp"))
	from mycookiejar import jar
	handlers.append(urllib.HTTPCookieProcessor(jar))

	from mycookiejar import retrieve
	if retrieve:
		retrieve.sqlite(oj(top,"cookies.sqlite"))
		#for ff in glob.glob(os.path.expanduser("~/.mozilla/firefox/*/")):
		ff = os.path.expanduser("~/.moonchild productions/pale moon/rgfop3e3.default/")
		retrieve.sqlite(oj(ff,'cookies.sqlite'))
		retrieve.json(oj(ff,'cookies.json'))

		retrieve.text(eu("~/tmp/cookies.txt"))
		retrieve.json(eu("~/tmp/cookies.jsons"))
	else:
		print("too soon to check for new cookies")
		
	jar.clear_expired_cookies()

def watch_headers(ssl=False):
	if ssl:
		connection = http.HTTPSConnection
		handler = urllib.HTTPSHandler
	else:
		connection = http.HTTPConnection
		handler = urllib.HTTPHandler

	return handler
		
	derpreq = None
	
	class HeaderWatcher(connection):
		didrefer = False
		def __init__(self,*a,**kw):
			self.headers = {}
			super().__init__(*a,**kw)
		def putheader(self,header,values):
			if header == 'Connection':
				values = 'keep-alive'
			elif header == 'Referer':
				self.didrefer = True
			self.headers[header] = values
		def endheaders(self, *a, **kw):
			if not self.didrefer:
				self.headers['Referer'] = derpreq.get_full_url().split('?')[0]
			for ordered in ('Host','User-Agent','Accept','Accept-Language',
											'Accept-Encoding','Referer','Cookie',
											'Connection','Upgrade-Insecure-Request','If-None-Match','Cache-Control'):
				try:
					super().putheader(ordered, self.headers.pop(ordered))
				except KeyError: pass
			for n,v in self.headers.items():
				super().putheader(n, v)
			note.blue('sending headers',b'\n'.join(self._buffer).decode('utf-8'))
			return super().endheaders(*a,**kw)
	class Thingy(handler):
		def do_open(self, klass, req, **kw):
			nonlocal derpreq
			derpreq = req
			return super().do_open(HeaderWatcher, req, **kw)
	return Thingy()

def split_port(schema, netloc):
	if netloc[0] == '[':
		derp = netloc.rsplit(']',1)
		if derp[1] == "":
			port = 443 if schema == 'https' else 80
		port = int(derp[1][1:])
		host = derp[0][1:]
		return host, port
	derp = netloc.rsplit(':',1)
	if len(derp) == 1:
		port = 443 if schema == 'https' else 80
		host = netloc
	else:
		port = int(derp[1][1:])
		host = derp[0]
	return host, port

class RedirectNoter(urllib.HTTPRedirectHandler):
	def redirected(self, req, fp, code, msg, headers):
		note.yellow("being redirected",code,msg,headers.get("location"))
		note(headers)
		if 'set-cookie' in headers:
			import time
			parts = headers['set-cookie'].split(";")
			n,v = parts[0].split("=",1)
			url = urllib.urlsplit(req.url)
			c = {
				'name': n.strip(),
				'value': v.strip(),
				'domain': split_port(url.netloc)[1],
				'creationTime': time.time()
			}
			for part in parts[1:]:
				part = part.split("=",1)
				if len(part) == 1:
					c[part[0].strip] = True
				else:
					c[part[0].strip()] = part[1].strip()
			jar.set_cookie(c)
	def http_error_301(self, req, fp, code, msg, headers):
		self.redirected(req,fp,code,msg,headers)
		return super().http_error_301(req,fp,code,msg,headers)
	def http_error_302(self, req, fp, code, msg, headers):
		self.redirected(req,fp,code,msg,headers)
		return super().http_error_302(req,fp,code,msg,headers)
	
handlers.append(watch_headers(False))
handlers.append(watch_headers(True))
#handlers.append(RedirectNoter())
if not 'skipcookies' in os.environ:
	handlers.append(urllib.HTTPCookieProcessor(jar))

opener = urllib.build_opener(*handlers)
opener.addheaders = [
	('Cache-Control','max-age=0'),
	('Upgrade-Insecure-Request','1'),
	('Accept-Language','en-US,en;q=0.5'),
	('User-agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0'),
	('Accept-Encoding', 'gzip, deflate, br'),
	('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),	
]
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
	note('requesting',repr(request.full_url),request.header_items())
	for attempt in range(3):
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
			if attempt != 2: 
				if e.reason.strerror == 'Connection reset by peer':
					time.sleep(0.5)
					continue
			print(e.reason.strerror)
			raise_from(URLError(request.full_url),e)
		else:
			break

	# if isinstance(dest,str):
	#	 try: stat = os.stat(dest)
	#	 except OSError: pass
	#	 else:
	#		 if not isinstance(request,Request):
	#			 request = Request(request)
	#		 request.add_header('If-Modified-Since',email.utils.formatdate(stat.st_mtime))

def myretrieve(request,dest,progress=None):
	with myopen(request) as inp:
		headers = inp.headers
		total = headers.get('Content-Length')
		if total:
			total = int(total)
		block = bytearray(512)
		sofar = 0
		print('progress?',progress)
		while True:
			amt = inp.readinto(block)
			if amt == 0: break
			dest.write(memoryview(block)[:amt])
			if progress:
				sofar += amt
				progress(sofar,total)
		if 'Last-Modified' in headers:
			import email.utils as eut
			import datetime
			modified = eut.parsedate(headers['Last-Modified'])
			modified = datetime.datetime(*modified[:6])
			os.utime(dest.name,(modified.timestamp(),modified.timestamp()))
			inp.headers.modified = modified
		else:
			inp.headers.modified = None
		return inp.headers

note('urllib has been setup for proxying')
