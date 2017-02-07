import tags,db,pages,create,filedb
tagsModule = tags
from user import User
from pages import d,RawString,Links

from replacer import replacerFile

import http.client as codes

import shutil,datetime
import email.utils
import os

def setup():
	db.setup('''CREATE TABLE uploads (	
	uzer INTEGER REFERENCES uzers(id) ON DELETE CASCADE ON UPDATE CASCADE,
	media INTEGER REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
	checked boolean DEFAULT FALSE)''',
	'''CREATE UNIQUE INDEX nodupesuploads ON uploads(uzer,media)''')

setup()

class Error(Exception): pass

def mycopy(src,dst,length=None):
	buf = bytearray(min(0x1000,length) if length else 0x1000)
	left = length
	while True:
		amt = src.readinto(buf)
		if amt <= 0: break
		dst.write(memoryview(buf)[:amt])
		if left is not None:
			left -= amt;
			if left < len(buf):
				buf = bytearray(left)

def get_filename(req):
	if 'X-File-Name' in req.headers:
		return req.headers['X-File-Name']
	if 'Content-Disposition' in req.headers:
		disposition = req.headers['Content-Disposition']
		value,params = cgi.parse_header(disposition)
		if 'filename' in params:
			if value != 'attachment':
				note.warning("Weird content disposition",disposition)
			return params['filename']
	name = req.path.rsplit('/',1)[-1]
	if not '.' in name:
		if not name:
			name = 'unknown'
		if 'Content-Type' in req.headers:
			content_type = cgi.parse_header(req.headers['Content-Type'])
			ext = magic.guess_extension(content_type) 
		else:
			ext = '.dat'
		name += ext
	return name

def manage(req):
	message = 'Uploaded.'
	name = get_filename(req)
	if len(name)>0x80:
		raise Error("That file name is too long.")
	# what unicode characters shouldn't be allowed in names?
	# name = ''.join(n for n in name if n in goodCharacters)
	name = name.encode('utf-8',errors='xmlcharrefreplace').decode('utf-8')

	sources = serv.headers.get_all('X-Source',())
	if sources:
		primarySource = sources[0]
	else:
		primarySource = None
	
	tags = serv.headers.get('X-Tags')
	if tags:
		tags = tagsModule.parse(tags)
	else:
		tags = ()
	for bit in serv.headers.get_all('X-Tag',()):
		if bit:			
			bit = tagsModule.parse(bit)
			if tags:
				tags.update(bit)
			else:
				tags = bit

	media = None

	length = serv.headers.get('Content-Length')
	if length is not None:
		try: length = int(length)
		except ValueError: pass
		if length == 0:
			# we're just submitting updates to an existing image.
			media = serv.headers.get("X-ID")
			if media:
				try:
					media = int(media,0x10)
				except ValueError: 
					try:
						media = int(media)
					except ValueError:
						raise Error("X-ID must be an integer")
			else:
				raise Error("Either upload a file or provide an X-ID header")
	else:
		if serv.headers.get('Transfer-Encoding') == 'chunked':
			raise Error("Please don't use chunked transfer encoding!")
		raise Error("Your client didn't set the Content-Length header for some reason.")

	if media is None:
		def download(dest):
			shutil.copyfileobj(self.rfile,dest,length)
			dest.flush()
			assert(dest.tell()>0)
			def getrawcreated():
				for header in (
						'X-Created',
						'Last-Modified',
						'If-Modified-Since'):
					if header in req.headers:
						return req.headers[header]
			created = getrawcreated()
			if created is None:
				return datetime.datetime.now()
			else:
				created = email.utils.parsedate(modified)
				return datetime.datetime(*(created[:6]))

		media, was_created = create.internet(download,
																				 None,
																				 tags,
																				 primarySource,
																				 sources,
																				 name)
	else:
		create.update(media,sources,tags,name)

	yield filedb.checkResized(media)
	if len(db.execute("SELECT uzer FROM uploads WHERE media = $1",(media,))) == 0:
		db.execute("INSERT INTO uploads (uzer,media) VALUES ($1,$2)",
							 (User.id,media))
		db.retransaction();
		message = 'Uploaded '+name+' to your queue for tagging.'
	else:
		message = 'You already seem to have uploaded this.'

	message = (message+'\r\n').encode('utf-8')
	req.send_response(codes.FOUND,"yay")
	req.send_header("Location","/~user/queue?message="+quote(message))
	req.end_headers()

	self.dest.seek(0,0)
	# close as we can get to when it was created...
	self.future.set_result(modified)
	# this closes the crab


def page(info,path,params):
	def contents():
		first = True
		for media, in db.execute('SELECT media FROM uploads WHERE uzer = $1 and checked = FALSE',(User.id,)):
			name,type,tags,sources = db.execute('''SELECT
			name,type,
			array(select name from tags where id = ANY(things.neighbors) ORDER BY name),
			array(select uri from urisources where id = ANY(media.sources) ORDER BY uri)
		FROM media
		INNER JOIN things ON media.id = things.id
		LEFT OUTER JOIN images ON images.id = media.id
	WHERE media.id = $1''',(media,))[0]
			media = filedb.checkResized(media)
			
			location = '/resized/'+media+'/donotsave.this'
			if first:
				first = False
			else:
				yield d.hr()
			yield d.p(media,d.br(),d.form(
				d.input(name='media',value=media,type='hidden'),
				d.input(name='type',value=type,type='hidden'),
				d.a(d.img(src=location,alt='Still resizing...'),href='/art/~page/'+media),
					d.div(
						"Tags",
						d.input(id='tags',name='tags',type='entry',value=', '.join(tags))),
					d.div(
						"Sources",
						d.textarea(RawString('\n'.join(sources)),name="sources")),
					d.div(d.button("Update")),
					enctype='multipart/form-data',
					method='POST'))
	with Links:
		Links.style = "/style/upload.css"
		return pages.makePage('Pending uploads',contents())

def addInfoToMedia(form,media=None):
	if not media:
		media = form.get('media')
		if not media: return
		media = int(media[0],0x10)
	dertags = form.get('tags')
	if not dertags: return
	sources = form.get('sources')	
	if not sources: return
	mime = form.get('type')
	# XXX: should do something with type
	if not mime: return
	dertags = tags.parse(dertags[0])
	sources = sources[0].split('\n')	

	with db.transaction():
		db.execute('UPDATE things SET neighbors = array(SELECT unnest(neighbors) UNION SELECT unnest($2::INTEGER[]) EXCEPT SELECT unnest($3::INTEGER[])) WHERE id = $1',
				(media,dertags.posi,dertags.nega))
		derp = []
		for source in sources:
			operation = 'UNION'
			if source and source[0] == '-':
				operation = 'EXCEPT'
				source = source[1:]
			derp.append(create.sourceId(source))
		db.execute("UPDATE media SET sources = array(SELECT unnest(sources) "+operation+" SELECT unnest($1::INTEGER[])) WHERE id = $2",(derp,media))
		db.execute("UPDATE uploads SET checked = TRUE WHERE uzer = $1 AND media = $2",(User.id,media))

def post(path,header,data):
	boundary = header['boundary']
	media = None
	if data and data.startswith(boundary):
		# we have a file included to upload.
		sources = form.get('sources')[0].split('\n')
		def download(dest):
			dest.write(data[:-(2+len(boundary))])
		media = create.internet(download,None,
				tags.parse(form.get('tags')[0]),
				sources[0],
				sources[1:],
				form.get('name')[0])
	addInfoToMedia(form,media)
	return '/art/~uploads'
