import create
import explanations
import setupurllib
import db
from better import print as _
import note
from description import describe

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

def parse(primarySource,noCreate=False,progress=None):
	primarySource = primarySource.strip()
	if (skip or noCreate):
		source = db.execute("SELECT id FROM media WHERE id = (SELECT id FROM urisources WHERE uri = $1)",(primarySource,))
		if source:
			note('skipping',primarySource)
			return source[0][0],False
	note('parsing',repr(primarySource))
	url = urllib.parse.urlparse(primarySource)
	for name,matcher,handlers in finders:
		if not matcher(url):
			continue
		
		if 'normalize' in handlers:
			normalize = handlers['normalize']
		else:
			normalize = lambda url: url

		sources = None
		name = None
		description = None
		explanations = []
		medias = None
		tags = None
	
		def doit():
			nonlocal sources, name, description, primarySource, medias, tags
			primarySource = normalize(primarySource)
			if 'json' in handlers:
				derp = handlers['json'](primarySource)
			else:
				derp = primarySource
			note("opening?",derp)
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
			sources = [primarySource]
			name = None
			description = None
			if 'json' in handlers:
				results = handlers['extract'](primarySource,headers,
				                              json.loads(doc.decode('utf-8')))
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
				elif isinstance(thing,Explanation):
					explanations.append(thing)
				elif isinstance(thing,Name):
					name = thing
				elif isinstance(thing,Description):
					description = thing
		try:
			while True:
				try:
					doit()
				except Redirect as r:
					primarySource = r.args[0]
				else:
					break
		except KeyError as e:
			note.error("uhhhh",e)
			continue
		except AttributeError as e:
			raise ParseError("Bad attribute") from e
		if not medias:
			note.red(name,primarySource,"No media. Failing...")
			continue
		if True:
			note("tags",[str(tag) for tag in tags])
			note("name",repr(name))
			note("desc",repr(description))
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
				note('download',media.url)
				response = myretrieve(Request(media.url,
																			headers=media.headers),
															dest,
															progress=progress)
				return response.modified, response["Content-Type"]
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
				if description:
					note("yay",description,wasCreated)
					@describe(image)
					def describing(olddesc,changed):
						if description != olddesc:
							changed(description)
				for e in explanations:
					print("explain",e)
					try:
						db.execute("INSERT INTO explanations (image,top,derpleft,w,h,script) VALUES ($1,$2,$3,$4,$5,$6)",
											 (image, e.top, e.left, e.width, e.height, e))
					except db.SQLError:
						print("already here")
						pass
				return image,wasCreated
			except create.NoGood:
				note.red("No good",media.url,media.headers)
				raise
	else:
		raise ParseError("Can't parse {}!".format(primarySource))

def normalize(url):
	burl = urllib.parse.urlparse(url)
	for name,matcher,handlers in finders:
		if matcher(burl):
			if 'normalize' in handlers:
				note('handler',handlers['normalize'])
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
	result = db.execute("SELECT id FROM media where sources @> array(select id from urisources WHERE uri = $1)",(uri,))
	if len(result)==0: return False
	return result[0][0], False

import time
def waitFor(uri,wait=time.sleep):
	while True:
		ah = alreadyHere(uri)
		if ah: return ah[0]
		note.alarm("No image found for",uri,"yet")
		wait(1)
