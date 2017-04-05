from favorites.things import *
import re
import urllib.parse

def mystrip(s,chars):
	for c in chars:
		i = s.rfind(c)
		if i >= 0:
			s = s[i+1:]
	return s

notags = re.compile('([0-9]+).*(\\..*)')

def fixCloudflareIdiocy(url):
	# cloudflare says 400 bad request, if there are urlencoded parentheses in a url
	url = url.replace('%28','').replace('%29','')
	return url

def tagoid(lookup):
	pat = None
	keys = tuple(lookup.keys())
	for key in keys:
		if pat is None:
			pat = ''
		else:
			pat += "|" 
		pat += "(?:" + key + "([^" + key + "\\n]+)" + key + ")"
	pat = re.compile(pat)
	def repl(m):
		for i in range(len(keys)):
			if m.group(i+1):
				tag = lookup[keys[i]]
				return '<' + tag + '>' + m.group(i+1) + '</' + tag + '>'
		raise RuntimeError("should have matched!")
	return lambda s: pat.sub(repl, s)

class parse:
	base = 'https://derpibooru.org'
	tags = tagoid({"_": 'i',
								 "\\*": 'b',
								 "\\+": 'u',
								 "-": 's'})
	links = re.compile('"([^"]+)":([^ ]+)')
	images = re.compile(">>([0-9]+)(t|s|p)?")
	lines = re.compile("\s*\n\s*")
	def parse(s):
		if s is None:
			return
		ret = ""
		for line in parse.lines.split(s):
			line = line.strip()
			if line:
				line = parse.parseLine(line).strip()
				if line:
					ret += '<p>' + line + '</p>\n'
		return ret
	def parseLine(s):
		import db
		ret = ""
		start = 0
		for m in parse.links.finditer(s):
			mstart, mend = m.span()
			ret += parse.parsePart(s[start:mstart])
			ret += '<a href=\"'+urllib.parse.urljoin(parse.base,m.group(2))+'">'+m.group(1)+'</a>'
			start = mend
		ret += s[start:]
		return ret
	def parsePart(s):
		s = parse.tags(s)
		def repl(m):
			uri = 'https://derpibooru.org/'+m.group(1)
			source = db.execute("SELECT id FROM urisources WHERE uri = $1",(uri,))
			def derp(href):
				return "<a href=\""+href+"\">&gt;&gt;"+m.group(1)+"</a>"
			if not source:
				return derp(uri)
			source = source[0][0]
			print(source)
			ident = db.execute("SELECT id FROM media WHERE sources @> ARRAY[$1::int]",(source,))
			if not ident:
				# huh?
				return derp(uri)
			ident = ident[0][0]
			return derp("/art/~page/{:x}".format(ident))
		s = parse.images.sub(repl, s)
		return s

def extract(primarySource, headers, doc):
	if not 'nodescription' in os.environ:
		desc = parse.parse(doc['description']).strip()
		if desc:
			yield Description(desc)
	for tag in doc['tags'].split(', '):
		if ':' in tag:
			yield Tag(*tag.split(':',1))
		else:
			yield Tag(None, tag)
	yield Name(doc['file_name'])
	# yield Type(doc['mime_type']) this gets sent during the request anyway
	yield Media(doc['image'])

import sys,os
here = os.path.dirname(sys.modules[__name__].__file__)

with open(os.path.join(here,'derpibooru.priv'),"rt") as inp:
	key = inp.read()

def find_json(url):
	return url + ".json?key=" + key

def normalize(url):
	u = urllib.parse.urlparse(url)
	host = u.netloc
	path = u.path
	if host == 'derpiboo.ru':
		host = 'derpibooru.org'
	elif host.endswith('derpicdn.net'):
		path,tail = path.rsplit('/',1)
		match = notags.match(tail)
		if match:
			path = path + '/' +  match.group(1) + match.group(2)
	elif not host.endswith('derpibooru.org'):
		return url

	if path.startswith('/images/'):
		path = path[len('/images'):]
		
	url = urllib.parse.urlunparse(('https',host,path,None,None,None))
	#raise SystemExit('okay',url)
	return url
