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

def extract(doc):
	print(doc)
	raise SystemExit

def find_json(url):
	return url + ".json"
		
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
