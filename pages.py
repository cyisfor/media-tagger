import fixprint

from dimensions import thumbnailPageSize,thumbnailRowSize

import comic
from user import User,dtags as defaultTags
from session import Session
import tags
from context import contextify
import db
from redirect import Redirect
import filedb

import process
from note import note
import explanations

from schlorp import schlorp

import mydirty as d
from dirty import RawString
from place import place
from itertools import count, chain
from contextlib import contextmanager, nested

try:
	from numpy import mean
except ImportError:
	def mean(l):
		i = 0
		s = 0
		for n in l:
			i += 1
			s += n
		return s / i

import re
import json
from urllib.parse import quote as derp, urljoin
import time
import os

import textwrap

maxWidth = 800
maxSize = 0x40000

def wrappit(s):
	return textwrap.fill(s,width=0x40)

def quote(s):
	try:
		# sigh...
		return derp(s).replace('/','%2f').replace('%3A',':')
	except:
		print(repr(s))
		raise

def comment(s):
	return RawString('<!-- '+s+' -->')

def stripPrefix(type):
	if type:
		a = type.split('/',1)
		if len(a)==2:
			return a[1]
		else:
			return 'jpeg'

def degeneralize(tag):
	if tag[:len('general:')]=='general:':
		return tag[len('general:'):]
	return tag

def spaceBetween(elements):
	first = True
	for e in elements:
		if first:
			first = False
		else:
			d.current_element.append(' ')
		yield e

def doTags(tags):
	for tag in spaceBetween(tags):
		d.a(tag,href=top+'/'+quote(tag)+'/')

def pageLink(id,i=0):
	return place+'/~page/'+'{:x}/'.format(id)

# Cannot set modified from the set of media in this because:
# If the 1st page has a newly added medium, the 3rd page will change,
# but the media on the 3rd page will still have older modified times.
# You'd need to request the first page AND the 3rd page, then just use the max modified from
# the first page, for every query. Could just request offset 0 limit 1 I guess...
# withtags.searchTags(tags,negatags,offset=0,limit=1,justModifiedField=True)
# XXX: do this, but write story for now.
# but then you add a tag to the 29th page medium, and page 30 changes but page 1 stays the same!

def tail(s,delim):
	i = s.rfind(delim)
	if i == -1:
		return s
	return s[i+1:]

assert tail("test.jpg",".")=='jpg'

def fixType(id):
	import derpmagic as magic
	import filedb
	info = magic.guess_type(filedb.mediumPath(id))
	type = info[0]
	if type == 'application/octet-stream':
		raise RuntimeError("Please inspect {:x} could not determine type!".format(id))
	db.execute("UPDATE media SET type = $1 WHERE id = $2",(type,id))
	return type

def fixName(id,type):
	for uri, in db.execute("SELECT uri FROM urisources INNER JOIN media ON media.sources @> ARRAY[urisources.id] AND media.id = $1",(id,)):
		name = tail(uri,'/').rstrip('.')
		if name: break
	else:
		name = 'unknown'

	if not '.' in name:
		if type == 'application/octet-stream':
			type = fixType(id)
		import derpmagic as magic
		name = name + magic.guess_extension(type)

	db.execute("UPDATE media SET name = $1 WHERE id = $2",(name,id))
	return name

def doneiterating(iter):
	def deco(final):
		for item in iter:
			yield item
		final()
	return deco

def makeLinks(info,linkfor=None):
	if linkfor is None:
		linkfor = pageLink
	counter = count(0)
	row = []
	rows = []
	allexists = True
	def row(id,name,type,tags,*is_comic):
		nonlocal allexists
		if len(is_comic) >= 1:
			is_comic = is_comic[0]
		else:
			is_comic = False
		i = next(counter)
		if i%thumbnailRowSize==0:
			if row:
				#rows.append(row)
				rows.append((tuple(row)+(d.br(),)))
			row = []
		tags = [str(tag) for tag in tags]
		if type == 'application/x-shockwave-flash':
			src = '/flash.jpg'
		else:
			fid,oneexists = filedb.check(id)
			allexists = allexists and oneexists
			src='/thumb/'+fid
		link = linkfor(id,i)
		if name is None:
			name = fixName(id,type)
		#row.append(d.td(d.a(d.img(src=src,alt="h",title=' '+name+' '),href=link),d.br(),d.sup('(i)',title=wrappit(', '.join(tags))) if tags else '',href=link))
		thingy = "(i)";
		taginfo = d.span(thingy,title=wrappit(', '.join(tags)
										   if tags else ''),
						 href=link,
						 class_='taghi')
		link = d.a(d.img(src=src,title=' '+name+' '),href=link)
		klass = 'thumb'
		if is_comic:
			klass += ' comic'
		yield d.div(link,taginfo,class_=klass)
	rows = (row(*r) for r in info)
	if len(info) > 0:
		rows = chain(rows,d.br)
	@doneiterating(rows)
	def result():
		Session.refresh = not allexists
	return result

def makeBase():
	# drop bass
	return 'http://[fcd9:e703:498e:5d07:e5fc:d525:80a6:a51c]/art/'

@contextify
class Links:
	next = None
	prev = None
	id = None

# meh
# style = schlorp(os.path.join(filedb.base,"style.css"),text=False)

@contextmanager
def standardHead(title,*contents):
	# oembed sucks:
	if Links.id:
		url = urljoin(makeBase(),'/art/~page/{:x}/'.format(Links.id))
	with d.head as head:
		d.title(title)
		d.meta(charset='utf-8')
		d.meta(name="og:title",value=title)
		d.meta(name="og:type",value="website")
		d.meta(name="og:image",value=("/thumb/{:x}".format(Links.id) if Links.id else "/thumb/5d359"))
		d.meta(name="og:url",value=url if Links.id else makeBase())
		d.link(rel="icon",type="image/png",href="/favicon.png")
		d.link(rel='stylesheet',type='text/css',href="/style/art.css")
		if Links.next:
			d.link(rel='next',href=Links.next)
		if Links.prev:
			d.link(rel='prev',href=Links.prev)
		if User.navigate:
			d.script(src="/stuff/navigation.js",type="text/javascript")

		if Links.id:
			d.link(rel='alternate',
			       type='application/json+oembed',
			       href='/art/~oembed/{:x}?url={}'.format(
				       Links.id,
				       # oembed sucks:
				       quote(url)))
		yield head

derpage = None
		
@contextmanager
def makePage(title,custom_head=False,douser=True):
	global derpage
	derpage = d.xhtml
	with derpage:
		if custom_head:
			with standardHead(title) as head:
				yield head,d.body
		else:
			standardHead(title)
			with d.body as body:
				yield body
				if not douser:
					d.p(d.a("User Settings",href=("/art/~user")))

def makeStyle(s):
	res = ''
	for selector,props in s:
		res += selector + '{\n';
		for n,v in props.items():
			res += '\t'+n+': '+v+';\n'
		res += '}\n'
	return d.style(res,type='text/css')

def makeLink(id,type,name,doScale,width=None,height=None,style=None):
	isImage = None
	if doScale:
		isImage = type.startswith('image')
		fid,exists = filedb.checkResized(id)
		resized = '/resized/'+fid+'/donotsave.this'
		Session.refresh = not exists and isImage
	else:
		fid = '{:x}'.format(id)
		resized = None

	if not style:
		if isImage is None:
			isImage = type.startswith('image')
		if not isImage:
			if width:
				style="width: "+str(width)+'px;'
			else:
				style = None
			if height:
				sty = ' height: '+str(height)+'px;'
				style = style + sty if style else sty

	thing = '/'.join(('/media',fid,type,name))

	if type.startswith('text'):
		return fid, d.pre(thing), thing
	if type.startswith('image'):
		if doScale:
			height = width = None # already resized the pixels
		if resized:
		  return fid, d.img(class_='wid',src=resized,alt='Still resizing...'), thing
		else:
			return fid, d.img(class_='wid',src=thing,style=style), thing
	# can't scale videos, so just adjust their width/height in CSS
	wrapper = None
	if type.startswith('audio') or type.startswith('video') or type == 'application/octet-stream':
		if type.endswith('webm') or type.endswith('ogg'):
			if type[0]=='a':
				wrapper = d.audio
			else:
				wrapper = d.video
			return fid,wrapper(d.source(src=thing,type=type),
					d.object(
						d.embed(src=thing,style=style,type=type),
						width=width, height=height,
						data=thing,style=style,type=type),
						autoplay=True,loop=True), thing
		else:
			return fid,(d.object(
					d.embed(' ',src=thing,style=style,type=type,loop=True,autoplay=True),
					d.param(name='src',value=thing),
						style=style,
						type=type,
						loop=True,
						autoplay=True,
						width=width,
						height=height),d.br(),"Download"),thing
	if type == 'application/x-shockwave-flash':
		return fid,(d.object(d.param(name='SRC',value=thing),
				embed(' ',src=thing,style=style),
				style=style),d.br(),'Download'),thing
	raise RuntimeError("What is "+type)

def mediaLink(id,type):
	return '/media/{:x}/{}'.format(id,type)

def simple(info,path,params):
	if Session.head: return
	id,type = info
	with makePage("derp"), d.a(href=pageLink(id)):
		d.img(class_='wid',
		      src=mediaLink(id,type))

def resized(info,path,params):
	id = int(path[1],0x10)
	while True:
		fid, exists = filedb.checkResized(id)
		if exists: break
	raise Redirect("/resized/"+fid+"/donotsave.this")

tagsModule = tags # sigh

def checkExplain(id,link,width,height,thing):
	style = [
			('#img', {
				'width': str(width)+'px',
				'height': str(height)+'px',
				}),
			('#img .exp', {
							'position': 'absolute',
				}),
			('#img .exp div', {
				'visibility': 'hidden',
				}),
			('#img .exp:hover div', {
							'visibility': 'visible',
				})]

	def getareas():
		for i,(aid,top,left,w,h,text) in enumerate(explanations.explain(id)):
			style.append(('#i'+str(i), {
				'top': top,
				'left': left,
				'width': w,
				'height': h,
			}))

			yield d.div(d.div(text),
						{'class': 'exp',
						 'id': 'i'+str(i),
						 'data-id':aid})

	link = d.a(link,id='mediumu',href=thing)
	areas = tuple(getareas())
	if areas:
		imgmap = (makeStyle(style),)+areas
		return d.div(link,id='img',*imgmap)
	else:
		return d.div(link,id='img')

linepat = re.compile('[ \t]*\n+\s*')
	
def maybeDesc(id):
	blurb = db.execute('SELECT blurb FROM descriptions WHERE id = $1',(id,))
	if blurb:
		blurb = blurb[0][0]
		if not blurb: return None
		if blurb[0] == '<':
			return d.div(RawString(blurb),
			             id='desc')
		lines = linepat.split(blurb)
		# assuming blurb is trusted!
		return d.div([d.p(RawString(p)) for p in lines],
					 id='desc')
	return None
	
def page(info,path,params):
	if Session.head:
		id,modified,size = info
	else:
		id,next,prev,name,type,width,height,size,modified,tags,comic = info

	doScale = not 'ns' in params
	doScale = doScale and User.rescaleImages and size >= maxSize

	if Session.head:
		if doScale:
			fid, exists = filedb.checkResized(id)
			Session.refresh = not exists and type.startswith('image')
		Session.modified = modified
		return
	Links.id = id
	Session.modified = modified
	if name:
		name = quote(name)
		if not '.' in name:
			name = name + '/untitled.jpg'
	else:
		name = 'untitled.jpg'
	tags = [str(tag) if not isinstance(tag,str) else tag for tag in tags]
	tags = [(degeneralize(tag),tag) for tag in tags]
	boorutags = " ".join(tag[0].replace(' ','_') for tag in tags)
	# even if not rescaling, sets img width unless ns in params
	fid,link,thing = makeLink(id,type,name,doScale,width,height)

	def pageURL(id):
		return '../{:x}'.format(id)

	with nested(Links(), makePage("Page info for "+fid)):
		d.comment("Tags: "+boorutags)
		link = checkExplain(id,link,width,height,thing)
		d.div(link)
		maybeDesc(id)
		d.p(d.a('Info',href=place+"/~info/"+fid))
		if comic:
			comic, title, prev, next = comic
			if next:
				next = pageURL(next)
				if not Links.next:
					Links.next = next
			if prev:
				prev = pageURL(prev)
				if not Links.prev:
					Links.prev = prev
		with d.p("Comic: ") as p:
			d.a(title,href=comicURL(comic))
			p.append(' ')
			if prev:
				d.a('<<',href=prev)
			if next:
				d.a('>>',href=next)
		if tags:
			with d.p("Tags: ") as p:
				for tag in tags:
					p.append("\n")
					d.a(tag[0],id=tag[1],class_='tag',href=place+"/"+quote(tag[0]))
		if next and not Links.next:
			Links.next = pageURL(next)+unparseQuery()
		if prev and not Links.prev:
			Links.prev = pageURL(prev)+unparseQuery()

def stringize(key):
	if hasattr(key,'isoformat'):
		return key.isoformat()
	elif isinstance(key,str):
		return key
	elif isinstance(key,bytes):
		return key.decode('utf-8')
	return str(key)

def thumbLink(id):
	return "/thumb/"+'{:x}'.format(id)

def info(info,path,params):
	Session.modified = info['sessmodified']
	if Session.head: return
	del info['sessmodified']
	import info as derp
	id = info['id']
	sources = info['sources']
	if sources is None:
		sources = ()
	else:
		sources = ((id,derp.source(id)) for id in sources)
		sources = [pair for pair in sources if pair[1]]
	keys = set(info.keys())
	keys.discard('id')
	keys.discard('sources')
	keys = sorted(keys)
	fid,exists = filedb.check(id)
	Session.refresh = not exists
	tags = [str(tag) if not isinstance(tag,str) else tag for tag in info['tags']]
	info['tags'] = ', '.join(tags)

	with makePage("Info about "+fid):
		with d.p as top:
			d.a(d.img(src=thumbLink(id)),d.br(),"Page",href=pageLink(id))
			with d.table(Class='info'):
				for key,value in keys.items():
					d.tr(d.td(key),d.td(stringize(value),id=key)
			d.hr()
			top.append("Sources")
			with d.div(id='sources'):
				for id,source in sources):
					d.p(d.a(source,href=source))

def like(info):
	return "Under construction!"

def unparseQuery(query={}):
	for n,v in Session.params.items():
		query.setdefault(n,v)
	result = []
	for n,v in query.items():
		if isinstance(v,list) or isinstance(v,tuple) or isinstance(v,set):
			for vv in v:
				result.append((n,vv))
		elif isinstance(v,int):
			result.append((n,'{:x}'.format(v)))
		else:
			result.append((n,v))
	if result:
		return '?'+'&'.join(n+'='+v for n,v in result)
	return ''

def tagsURL(tags,negatags):
	if not (tags or negatags): return place+'/'
	res = place+'/'+"/".join([quote(tag) for tag in tags]+['-'+quote(tag) for tag in negatags])+'/'
	return res

def stripGeneral(tags):
	return [tag.replace('general:','') for tag in tags]

def media(url,query,offset,pageSize,info,related,basic):
	#related = tags.names(related) should already be done
	basic = tags.names(basic)
	related=stripGeneral(related)

	removers = []

	with Links():
		info = tuple(info)
		print('oooooo',offset)
		if len(info)>=pageSize:
			query['o'] = offset + 1
			Links.next = url.path+unparseQuery(query)
		if offset > 0:
			query['o'] = offset - 1
			Links.prev = url.path+unparseQuery(query)
		links = makeLinks(info)
		with makePage("Media "+str(basic)):
			d.p("You are ",d.a(User.ident,href=place+"/~user"))
			if links:
				d.div(links,id='thumbs')
			if related:
				with d.div("Related tags",d.hr(),id='related'):
					doTags(url.path.rstrip('/'),related)
			if basic.posi or basic.nega:
				with d.div("Remove tags",d.hr(),id='remove'):
					for tag in spaceBetween(basic.posi):
						d.a(tag,
						    href=tagsURL(basic.posi.difference(set([tag])),
						                 basic.nega))
					for tag in spaceBetween(tags.nega):
						d.a('-'+tag,
						    href=tagsURL(basic.posi,
						                 basic.nega.difference(set([tag]))))
			if Links.prev or Links.next:
				with d.p as p:
					if Links.prev:
						d.a('Prev',href=Links.prev)
						if Links.next:
							p.append(' ')
					if Links.next:
						d.a('Next',href=Links.next)

def notempty(it):
	it = iter(it)
	first = next(it)
	return chain((first,)it)
						
def clump(it,n=8):
	it = iter(it)
	while True:
		yield notempty(islice(it,n))
						
def desktop(raw,path,params):
	if 'n' in params:
		n = int(params['n'][0],0x10)
	else:
		n = 0x10
	import desktop
	history = desktop.history(n)
	if not history:
		return "No desktops yet!?"
	if 'd' in params:
		raise Redirect(pageLink(0,history[0]))
	return desktop_base(history,"/",None,pageLink)
	
def desktop_base(history,base,progress,pageLink):
	if Session.head:
		Session.modified = db.execute("SELECT EXTRACT(EPOCH FROM modified) FROM media WHERE media.id = $1",(history[0],))[0][0]
		return
	def makeDesktopLinks():
		nonlocal pageLink
		allexists = True
		for id,name in db.execute("SELECT id,name FROM media WHERE id = ANY ($1::bigint[])",(history,)):
			fid,exists = filedb.check(id)
			if progress:
				pageLink = progress(fid,name,exists)
			allexists = allexists and exists
			yield d.td(d.a(d.img(title=name,src=base+"thumb/"+fid),
			               href=pageLink(id)))
		Session.refresh = not allexists
	with makePage("Current Desktop"):
		if n == 0x10:
			current = history[0]
			history = history[1:]
			name,type,tags = db.execute("SELECT name,type,array(select name from tags where tags.id = ANY(neighbors)) FROM media INNER JOIN things ON things.id = media.id WHERE media.id = $1",(current,))[0]
			tags = [str(tag) for tag in tags]
			type = stripPrefix(type)
			d.p("Having tags ",doTags(place,tags))
			with nested(d.p, d.a(href=pageLink(current,0))):
				d.img(class_='wid',
				      src=base+"/".join((
					      "media",'{:x}'.format(current),type,name)))				
			d.hr()

			d.p("Past Desktops")
			with nested(d.div, d.table):
				for links in clump(makeDesktopLinks(),8):
					d.tr(*links)
	Session.modified = db.execute("SELECT EXTRACT (epoch from MAX(added)) FROM media")[0][0]

def user(info,path,params):
	if Session.head: return
	if 'submit' in params:
		process.user(path,params)
		raise Redirect(place+'/~user')
	iattr = {
			'type': 'checkbox',
			'name': 'rescale'}
	if User.rescaleImages:
		iattr['checked'] = True
	rescalebox = d.input(iattr)
	iattr = {
		'type': 'checkbox',
		'name': 'comic',
	}
	if not User.noComics:
		iattr['checked'] = True
	comicbox = d.input(iattr)

	iattr = {
		'type': 'checkbox',
		'name': 'navigate'
	}
	if User.navigate:
		iattr['checked'] = True
	navbox = d.input(iattr)
	if User.defaultTags:
		def makeResult():
			result = db.execute("SELECT tags.name FROM tags WHERE id = ANY($1::bigint[])",(defaultTags.posi,))
			for name in result:
				yield name[0],False
			result = db.execute("SELECT tags.name FROM tags WHERE id = ANY($1::bigint[])",(defaultTags.nega,))
			for name in result:
				yield name[0],True
		result = makeResult()
	else:
		result = db.execute('SELECT tags.name,uzertags.nega FROM tags INNER JOIN uzertags ON tags.id = uzertags.tag WHERE uzertags.uzer = $1',(User.id,))
		note('raw uzer tag result',result)
		result = ((row[0],row[1] is True or row[1]=='t') for row in result)
	tagnames = []
	for name,nega in result:
		if nega:
			name = '-'+name
		tagnames.append(name)
	tagnames = ', '.join(tagnames)
	note('tagnames',tagnames)
	def li(name,*a,**kw):
		d.tr(d.td(name),d.td(*a,**kw))
	with makePage("User Settings",douser=False):
		with nested(
	            d.form(action=place+'/~user/',
	                   type='application/x-www-form-urlencoded',
	                   method="post"),
	            d.table):
			li("Rescale Media? ",rescalebox)
			li("Comic pages on main listing? ",comicbox)
			li("Javascript navigation?",navbox,title="(This requires javascript!)")
			li("Implied Tags",d.input(type='text',name='tags',value=tagnames))
			li(d.input(type="submit",value="Submit"))
		with d.p:
			d.a('Main Page',href=place)

def getPage(params):
	page = params.get('p')
	if not page:
		return 0
	else:
		return int(page[0])

def getType(medium):
	return db.execute("SELECT type FROM media WHERE id = $1",(medium,))[0][0]

def getStuff(medium):
	return db.execute('''SELECT
	type,
	size,
	COALESCE(images.width,videos.width),
	COALESCE(images.height,videos.height)
	FROM media
	LEFT OUTER JOIN images ON media.id = images.id
	LEFT OUTER JOIN videos ON media.id = videos.id
	WHERE media.id = $1''',(medium,))[0]

def comicPageLink(com,isDown=False):
	def pageLink(medium=None,counter=None):
		if isDown:
			link = ''
		else:
			link = '../'
		link = link + '{:x}/'.format(com)
		return link + unparseQuery()
	return pageLink

def comicNoExist():
	raise RuntimeError("Comic no exist")

def checkModified(medium):
	modified = db.execute('SELECT EXTRACT(EPOCH FROM modified) FROM media WHERE id = $1',(medium,))[0][0]
	if modified:
		if Session.modified:
			Session.modified = max(modified,Session.modified)
		else:
			Session.modified = modified

def showAllComics(params):
	page = getPage(params)
	comics = comic.list(page,User.tags().nega)
	def getInfos():
		for id,title,tagids,tags in comics:
			try:
				medium = comic.findMedium(id,0)
			except Redirect:
				medium = 0x5c911
			if not medium:
				medium = 0x5c911
			checkModified(medium)
			yield medium,title,getType(medium),tags or ()
	if Session.head:
		for stuff in getInfos(): pass
		return
	with Links():
		if page > 0:
			Links.prev = unparseQuery({'p':page-1})
		if page + 1 < comic.numComics() / 0x20:
			Links.next = unparseQuery({'p':page+1})
		def formatLink(medium,i):
			if comic.pages(comics[i][0]) == 0:
				return '{:x}/'.format(comics[i][0])
			return '{:x}/0/'.format(comics[i][0])
		with makePage("{:x} Page Comics".format(page),
		              custom_head=True) as head,body:
			with head:
				makeLinks(getInfos(),formatLink)
			with body:
				with d.p as p:
					if Links.prev:
						d.a("Prev",href=Links.prev)
						if Links.next:
							p.append(' ')
					if Links.next:
						d.a("Next",href=Links.next)

def showPages(path,params):
	com = int(path[0],0x10)
	page = getPage(params)
	offset = page * 0x20
	if offset and offset >= comic.pages(com):
		raise Redirect('..')
	numPages = comic.pages(com)
	def getMedia():
		for which in range(offset,min(0x20+offset,numPages)):
			medium = comic.findMedium(com,which)
			checkModified(medium)
			yield medium,which
	if Session.head:
		for stuff in getMedia(): pass
		return
	title,description,source,tags = comic.findInfoDerp(com)[0]
	if not description: description = 'ehunno'
	def getInfos():
		for medium,which in getMedia():
			yield medium,title + ' page {}'.format(which),getType(medium),()
	with Links():
		if page > 0:
			Links.prev = unparseQuery({'p':page-1})
		if page + 1 < numPages:
			Links.next = unparseQuery({'p':page+1})
		with makePage(title + " - Comics"):
			d.h1(title)
			consume(makeLinks(
				getInfos(),
				lambda medium,i: '{:x}/'.format(i+offset)))

			d.p(RawString(description)),
			d.p("Tags:",", ".join(tags)),
			if source:
				d.p(d.a('Source',href=source))
			with d.p:
				if Links.prev:
					d.a("Prev ",href=Links.prev)
				d.a("Index",href="..")
				if Links.next:
					d.a(" Next",href=Links.next)

def showComicPage(path):
	com = int(path[0],0x10)
	which = int(path[1],0x10)
	medium = comic.findMedium(com,which)
	checkModified(medium)
	if Session.head: return
	title,description,source,tags = comic.findInfoDerp(com)[0]
	typ,size,width,height = getStuff(medium)
	name = title + '.' + typ.rsplit('/',1)[-1]
	with Links():
		if which > 0:
			Links.prev = comicPageLink(which-1)()
		if comic.pages(com) > which+1:
			Links.next = comicPageLink(which+1)()
		else:
			Links.next = ".."
		medium = comic.findMedium(com,which)
		doScale = User.rescaleImages and size >= maxSize
		fid,link,thing = makeLink(medium,typ,name,
				doScale,style='width: 100%')
		link = checkExplain(medium,link,width,height,Links.next)
		with makePage("{:x} page ".format(which)+title):
			d.div(link)
			maybeDesc(medium)
			with d.p:
				if Links.prev:
					d.a("Prev ",href=Links.prev)
				d.a("Index",href="..")
				if Links.next:
					d.a(" Next",href=Links.next)
			with d.p:
				d.a("Page",href="/art/~page/"+fid)
				p.append(' ')
				if doScale:
					d.a("Medium",href=link)
			d.p("Tags: ",", ".join(tags))

def showComic(info,path,params):
	path = path[1:]
	if len(path) == 0:
		return showAllComics(params)
	elif len(path) == 1:
		return showPages(path,params)
	else:
		return showComicPage(path)

def oembed(info, path, params):
	Session.type = 'application/json'
	if Session.head: return
	id,tags = info
	base = makeBase()
	xid, exists = filedb.check(id)
	thumb = urljoin(base,thumbLink(id))
	response = {
			'type': 'photo',
			'tags': tags,
			'version': 1.0,
			'url': thumb,
			'width': 150,
			'height': 150,
			'thumbnail_url': thumb,
			'thumbnail_width': 150,
			'thumbnail_height': 150,
			'provider_url': base,
			}
	return json.dumps(response)
