import create
import setupurllib
import db
import fixprint
import note

import json
from bs4sux import BeautifulSoup
import urllib.parse
import urllib.request
from setupurllib import myretrieve,myopen
import tempfile
import shutil

Request = urllib.request.Request

import os
import datetime
from pprint import pprint

try: from .things import *
except SystemError:
	from things import *

finders = []

skip = os.environ.get('skip')

def displayit(f):
	def wrap(*a,**kw):
		r = f(*a,**kw)
		print("GINOUH",f,a,kw,'=>',r)
		return r
	return wrap

def locked(table):
	def deco(f):
		def wrapper(*a,**kw):
			try:
				with db.transaction():
					note.blue('locking',table)
					try:
						db.execute('LOCK TABLE '+table+' IN EXCLUSIVE MODE NOWAIT')
					except db.ProgrammingError:
						# something else is handling this URL...
						raise
					note.blue('locked',table,f,a,kw)
					return f(*a,**kw)
			finally:
				note.alarm('unlocked',table)
		return wrapper
	return deco

def parse(primarySource,noCreate=False):
	note.alarm("uhhh")
	primarySource = primarySource.strip()
	if (skip or noCreate):
		source = db.execute("SELECT id FROM urisources WHERE uri = $1",(primarySource,))
		if source:
			note('skipping',primarySource)
			return db.execute('SELECT id FROM media WHERE sources @> ARRAY[$1::int]',(source[0]))[0][0]
	note('parsing',repr(primarySource))
	url = urllib.parse.urlparse(primarySource)
	doc = None
	for name,matcher,handlers in finders:
		if not matcher(url): continue
		
		if 'normalize' in handlers:
			normalize = handlers['normalize']
		else:
			normalize = lambda url: url
		primarySource = normalize(primarySource)
		if 'json' in handlers:
			derp = handlers['jsonuri'](primarySource)
		else:
			derp = primarySource
		with myopen(derp) as inp:
			headers = inp.headers
			if 'json' in handlers:
				if not headers.get('Content-Type').startswith('application/json'):
					raise ParseError(primarySource,'not json')
			else:
				if not headers.get('Content-Type').startswith('text/html'):
					raise ParseError(primarySource,"not html")													
			doc = inp.read()
		medias = []
		def generalize(tag):
			if isinstance(tag,Tag): return tag
			try:
				if len(tag) == 2:
					if len(tag[0]) >= 3 and len(tag[1]) >= 3:
						return Tag(*tag)
			except TypeError: pass
			if ':' in tag:
				return Tag(*(tag.split(':')))
			return Tag(None,tag)
		tags = [generalize(tag) for tag in handlers.get('tags',[])]
		if skip and db.execute("SELECT id FROM urisources WHERE uri = $1",(primarySource,)):
			note('skipping',primarySource)
			return
		sources = [primarySource]
		name = None
		try:
			if 'json' in handlers:
				results = handlers['json'](primarySource,headers,json.decode(doc))
			else:
				doc = BeautifulSoup(doc)
				setattr(doc,'url',primarySource)
				results = handlers['extract'](doc)
			for thing in results:
				if isinstance(thing,Tag):
					tags.append(thing)
				elif isinstance(thing,Media):
					medias.append(thing)
				elif isinstance(thing,Source):
					sources.append(thing)
				elif isinstance(thing,Name):
					name = thing
		except AttributeError as e:
			raise ParseError("Bad attribute") from e
		if not medias:
			note.red(name,primarySource,"No media. Failing...")
			continue
		if True:
			note("tags",[str(tag) for tag in tags])
			note("name",repr(name))
			note("Media",len(medias))
			note("PSource",primarySource)
			note("Sources",sources)
		for media in medias:
			derpmedia = normalize(media.url)
			derpSources = [normalize(source) for source in sources] + [derpmedia]
			media.url = urllib.parse.urljoin(primarySource,media.url)
			if len(medias) == 1:
				derpSource = primarySource
			else:
				derpSource = derpmedia
			derpSources = [create.Source(
				urllib.parse.urljoin(primarySource,source)) for source in derpSources]
			media.headers['Referer'] = primarySource
			def download(dest):
				print('download',media.url)
				myretrieve(Request(media.url,
					headers=media.headers),
					dest)
				dest.seek(0,0)
				mtime = os.fstat(dest.fileno()).st_mtime
				return datetime.datetime.fromtimestamp(mtime)
			# def download(dest):
			#	 with open('/tmp/derp.image','rb') as inp:
			#		 shutil.copyfileobj(inp,dest)
			#		 dest.seek(0,0)
			#		 mtime = os.fstat(inp.fileno()).st_mtime
			#	 return datetime.datetime.fromtimestamp(mtime)
			assert derpSource
			try:
				image,wasCreated = create.internet(download,
																					 create.Source(media.url),
																					 tags,
																					 create.Source(derpSource),
																					 derpSources,
																					 name = name)
				return image
			except create.NoGood:
				print("No good",media.url,media.headers)
				raise
	else:
		raise ParseError("Can't parse {}!".format(primarySource))

def normalize(url):
	burl = urllib.parse.urlparse(url)
	for name,matcher,handlers in finders:
		if matcher(burl):
			if 'normalize' in handlers:
				print('handler',handlers['normalize'])
				return handlers['normalize'](url)
			return url
	return url

class ParseError(RuntimeError): pass

def matchNetloc(s):
	def matcher(url):
		return url.netloc.endswith(s)
	return matcher

def registerFinder(matcher,handler,name=None):
	if name is None: name = matcher
	if hasattr(matcher,'search'):
		temp = matcher
		matcher = lambda url: temp.search(url.netloc)
	elif callable(matcher): pass
	else:
		matcher = matchNetloc(matcher)
	finders.append((name,matcher,handler))

def alreadyHere(uri):
	result = db.execute("SELECT id FROM urisources WHERE uri = $1",(uri,))
	if len(result)==0: return False
	return True
