import signal_debugging

from locks import processLocked
import db
from versions import Versioner
import tags
import filedb
import movie
import note

from imagecheck import NoGood,isGood
from weirdui import manuallyGetType

import imageInfo

from hashlib import sha1 as SHA,md5 as MD5

import gzip
import derpmagic as magic
import base64
import shutil
import datetime
import re
import os
import subprocess
import time

version = Versioner('create')
@version(1)
def refcounting():
	print('Implementing reference counting')
	db.vsetup(*db.source('sql/refcounting.sql',False))
	db.execute('SELECT refcountingsetup()')
	while True:
		start = time.time()
		count = db.execute('SELECT refcountingdiscover()')[0][0]
		end = time.time()
		if count == 0:
			break
		print('Discovered references for ',count,int(10*(end-start))/10)
		time.sleep(end-start)
	db.execute('SELECT refcountingfinish()')

@version(2)
def qualifiedSources():
	print('Differentiating sources that provide tags, and sources that uniquely identify media')
	db.setup('''ALTER TABLE sources ADD COLUMN hasTags boolean default FALSE NOT NULL''',
			 '''ALTER TABLE sources ADD COLUMN uniquelyIdentifies boolean default TRUE''')

version.setup()

class writer:
	def __init__(self, write):
		# pythoooon
		self.write = write

def mediaHash(data):
	digest = SHA()
	shutil.copyfileobj(data,writer(digest.update))
	digest = digest.digest()
	digest = base64.b64encode(digest)
	digest = digest.decode().rstrip('=')
	return digest

def sourceId(source,isUnique=True,hasTags=False):
	assert source is not None
	assert not isinstance(source,int)

	if source == '': return None
	if source[0] == '/': return None # todo: file sources?
	with db.transaction():
		id = db.execute("SELECT id FROM urisources WHERE uri = $1",(source,))
		if id:
			return id[0][0]
		else:
			id = db.execute("INSERT INTO sources (hasTags,uniquelyIdentifies) VALUES ($1,$2) RETURNING id",(hasTags,isUnique))
			id = id[0][0]
			db.execute("INSERT INTO urisources (id,uri) VALUES ($1,$2) RETURNING id",(id,source))
		return id

findMD5 = re.compile("\\b[0-9a-fA-F]{32}\\b")

def openImage(data):
	if isinstance(data,str):
		return imageInfo.get(data)
	try: return imageInfo.get(data.name)
	except imageInfo.Error:
		import sys
		et,e,tb = sys.exc_info()
		if e['reason'].startswith('no decode delegate for this image format'):
			return None,None
		raise
	except Exception as e:
		data.seek(0,0)
		note.alarm('Error reading image info',e)
		note(repr(data.read(20)))
		raise

def createImageDBEntry(id,image):
	db.execute("INSERT INTO images (id,animated,width,height) VALUES ($1,$2,$3,$4)",(id,)+image)

def retryCreateImage(id):
	source = filedb.mediaPath(id)
	image,type = openImage(source)
	if image:
		createImageDBEntry(id,image)
	return image,type

class SourceImpl:
	uri = None
	path = None
	id = None
	def __init__(self,thing):
		if isinstance(thing,int):
			self.id = thing
			return
		if hasattr(thing,'decode'):
			thing = thing.decode('utf-8')
		if ':' in thing and not '\\' in thing:
			self.uri = thing
		else:
			self.path = thing
	def lookup_id(self):
		if self.id: return self.id

		if self.uri:
			return sourceId(self.uri,self.isUnique,self.hasTags)
		assert(self.path)
		return db.execute("SELECT id FROM filesources WHERE path = $1",
		                  (self.path,))[0][0]
	def lookup_path(self):
		if self.path is None:
			assert self.id
			res = db.execute("SELECT path FROM filesources WHERE id = $1",
			                 (self.id,))
			if res:
				self.path = res[0][0]
		return self.path
	def lookup_uri(self):
		if self.uri is None:
			assert self.id
			res = db.execute("SELECT uri FROM urisources WHERE id = $1",
			                 (self.id,))
			if res:
				self.uri = res[0][0]
		return self.uri

class Source:
	def __init__(self,thing, isUnique=True,hasTags=False):
		self.hasTags = hasTags
		self.isUnique = isUnique
		self.impl = SourceImpl(thing)
	def __getattr__(self,name):
		if name == 'uri':
			self.id
			self.uri = self.impl.lookup_uri()
			return self.uri
		elif name == 'path':
			self.id
			self.path = self.impl.lookup_path()
			return self.path
		elif name == 'id':
			self.impl.hasTags = self.hasTags
			self.impl.isUnique = self.isUnique
			self.id = self.impl.lookup_id()
			return self.id
		else:
			return getattr(self.impl,name)

def getanId(sources,uniqueSources,download,name):
	for uniqueSource in uniqueSources:
		result = db.execute("SELECT id FROM media where media.sources @> ARRAY[$1::integer]",(uniqueSource.id,))
		if result:
			return result[0][0], False
	md5 = None
	for i,source in enumerate(sources):
		if source.uri:
			m = findMD5.search(source.uri)
			if m:
				md5 = m.group(0)
				result = db.execute("SELECT id FROM media WHERE md5 = $1",
							(md5,))
				if result:
					return result[0][0],False
				# don't return here!
				# we found an md5 and it wasn't in our database
				# so download it!
	note("downloading to get an id")
	with filedb.mediaBecomer() as data:
		created,mimetype = download(data)
		note('cerated',created)
		data.seek(0,0)
		digest = mediaHash(data)
		result = db.execute("SELECT id FROM media WHERE hash = $1",(digest,))
		if result:
			print("Oops, we already had this one, from another source!")
			return result[0][0],False
		result = db.execute("SELECT medium FROM dupes WHERE hash = $1",(digest,))
		if result:
			id = result[0][0]
			print("Dupe of {:x}".format(id))
			return id, False
		result = db.execute("SELECT id FROM blacklist WHERE hash = $1",(digest,))
		if result:
			# this hash is blacklisted
			raise NoGood("blacklisted",digest)
		if md5 is None:
			data.seek(0,0)
			md5 = MD5()
			shutil.copyfileobj(data,writer(md5.update))
			md5 = md5.hexdigest()
		with db.transaction():
			id = db.execute("INSERT INTO things DEFAULT VALUES RETURNING id")
			id = id[0][0]
			image = None
			data.seek(0,0)
			savedData = data
			image,derp = openImage(data)
			if mimetype is None:
				mimetype = derp
			if mimetype is None:
				if not image:
					note('we hafe to guess')
					try:
						mimetype = magic.guess_type(data.name)[0]
					except TypeError:
						mimetype = manuallyGetType(data, mimetype)
					else:
						if mimetype is None or mimetype == 'binary':
							mimetype = manuallyGetType(data,mimetype)
						else:
							mimetype = mimetype.split('\\012')[0]

					note.blue('guessed mimetype',repr(mimetype),type(mimetype))
				if not isGood(mimetype):
					mimetype = manuallyGetType(data,mimetype)
			if not '.' in name:
				name += '.' + magic.guess_extension(mimetype)
			note("New {} with id {:x} ({})".format(mimetype,id,name))
			sources = set([source.id for source in sources])
			db.execute("INSERT INTO media (id,name,hash,created,size,type,md5,sources) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)",(
				id,name,digest,created,
				os.fstat(data.fileno()).st_size,mimetype,md5,sources))
			if image: createImageDBEntry(id,image)
			else:
				if mimetype.startswith('video'):
					movie.isMovie(id,data)
				else:
					print(RuntimeError('WARNING NOT AN IMAGE OR MOVIE {:x}'
					                   .format(id)))
			data.flush()
			if hasattr(created,'timestamp'):
				timestamp = created.timestamp()
			else:
				import time
				timestamp = time.mktime(created.timetuple())
			os.utime(data.name,(timestamp,timestamp))
			data.become(id)


			# create thumbnail proactively
			# don't bother waiting for it to appear
			filedb.incoming(id)
			return id,True

tagsModule = tags

def update(id,sources,tags,name):
	donetags = []
	with db.transaction():
		db.execute("UPDATE media SET name = coalesce($3,name), sources = array(SELECT unnest(sources) from media where id = $2 UNION SELECT unnest($1::bigint[])), modified = clock_timestamp() WHERE id = $2",([source.id for source in sources],id,name))

	tagsModule.tag(id,tags)

def internet(download,media,tags,primarySource,otherSources,name=None):
	if not name:
		name = media.uri.rsplit('/',1)
		if len(name) == 2:
			name = name[1]
		else:
			name = name[0]
	uniqueSources = set()
	uniqueSources.add(media)
	uniqueSources.add(primarySource)
	if not uniqueSources:
		raise RuntimeError("No unique sources in this attempt to create?")
	note('name is',name)
	otherSources = set(otherSources)
	for source in otherSources: source.isUnique = False
	sources = uniqueSources.union(otherSources)
	with db.transaction():
		id,was_created = getanId(sources,uniqueSources,download,name)
	print('got id',hex(id),was_created)
	if not was_created:
		note("Old medium with id {:x}".format(id))
		#input()
	note("update")
	update(id,sources,tags,name)
	return id, was_created

def copyMe(source):
	def download(dest):
		shutil.copy2(source,dest.name)
		return datetime.datetime.fromtimestamp(os.fstat(dest.fileno()).st_mtime), None
	return download
