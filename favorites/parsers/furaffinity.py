from favorites.parse import ParseError
from favorites.things import *
import filedb
import re
import urllib.parse
from setupurllib import myretrieve
import os

def mystrip(s,chars):
	for c in chars:
		i = s.rfind(c)
		if i >= 0:
			s = s[i+1:]
	return s

kwMatch = re.compile('/search/@keywords (.*)')

def extract(doc):
	linx = doc.find('div',id='keywords')
	if linx:
		for a in linx.findAll('a'):
			href = a.get('href')
			if not href: continue
			m = kwMatch.match(href)
			if not m: continue
			yield Tag(None,m.group(1).lower())
	def fixProfile(profile):
		src = profile['src']
		if not urllib.parse.urlsplit(src).host.endsWith('facdn.net'): return
		name = src.rsplit('/',1)[-1]
		dest = os.path.join(filedb.base,'media','furaffinity')
		try: os.mkdir(dest)
		except OSError: pass
		dest = os.path.join(dest,urllib.parse.unquote(name))
		if not os.path.exists(dest):
			note("Need to get furaffinity image",src)
			myretrieve(src,dest)
		profile['src'] = '/media/furaffinity/' + name
	desc = doc.find('table',{'class':'maintable'})
	if desc:
		desc = desc.find('td',{'class': 'alt1'})
		for profile in desc.findAll('img'):
			fixProfile(profile)
			
	auth = doc.findAll('td',{'class':'cat'})
	if not auth or len(auth) < 2:
		with open('/tmp/furafffail.html','wt') as out:
			out.write(doc.prettify())
		raise ParseError("No author on furaffinity?")
	auth = auth[1]
	for a in auth.findAll('a'):
		href = a.get('href')
		if not href: continue
		if not href.startswith('/user/'): continue
		yield Tag('artist',href[len('/user/'):].rstrip('/'))
	for a in doc.findAll('a'):
		if not a.contents: continue
		if not 'Download' == str(a.contents[0]).strip(): continue
		href = a.get('href')
		if not href: continue
		yield Image(href)
def normalize(url):
	return url.replace('/full/','/view/')
