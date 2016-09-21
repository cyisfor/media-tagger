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

proxy = urllib.ProxyHandler({"http": "http://127.0.0.1:8123"})
handlers = [proxy]

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
		ff = os.path.expanduser("~/.mozilla/firefox/aoeu.default")
		retrieve.sqlite(oj(ff,'cookies.sqlite'))
		retrieve.json(oj(ff,'cookies.jsons'))

		retrieve.text("/extra/user/tmp/cookies.txt")	
		retrieve.json("/extra/user/tmp/cookies.jsons")
	else:
		print("too soon to check for new cookies")
		
	jar.clear_expired_cookies()

class HeaderWatcher(urllib.HTTPHandler):
	class Client(http.HTTPConnection):
		def request(self,method,selector,data,headers):
			print('sending headers',headers)
			super().request(method,selector,data,headers)
	def http_open(self, req):
		return self.do_open(self.Client, req)

class RedirectNoter(urllib.HTTPRedirectHandler):
	def http_error_302(self, req, fp, code, msg, headers):
		print("being redirected",code,msg,headers.get("location"))
		print(fp.read())
		super().http_error_302(req,fp,code,msg,headers)
	
handlers.append(HeaderWatcher())
handlers.append(RedirectNoter())

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
	global progress
	with myopen(request) as inp:
		headers = inp.headers
		total = headers.get('Content-Length')
		if total:
			total = int(total)
		block = bytearray(0x1000)
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
			os.utime(dest.name,(eut,eut))
			inp.headers.modified = modified
		else:
			inp.headers.modified = None
		return inp.headers

print('urllib has been setup for proxying')
