from favorites.things import *
import re
import urllib.parse

def mystrip(s,chars):
	for c in chars:
		i = s.rfind(c)
		if i >= 0:
			s = s[i+1:]
	return s

# can't use json because it discards all tag categories...

notestyle = re.compile("(width|height|top|left): ([0-9]+)px")

def extract(doc):
	gotImage = False
	for note in doc.findAll(attrs={'class':'note-box'}):
		class dims: pass
		for n,v in notestyle.findall(note['style']):
			setattr(dims,n,int(v))
		print(dims.height)
		raise SystemExit
	for li in doc.findAll('li'):
		for klass in li.attrs.get('class',()):
			if isinstance(klass,str):
				klass = (klass,)
			if klass and klass[0].startswith('tag-type-'):
				foundTag = False
				category = klass[0][len('tag-type-'):]
				anchors = li.findAll('a')
				for a in anchors:
					if len(a.contents)>0:
						if a.contents[0] == '?':
							foundTag = True
							yield Tag(category,urllib.parse.unquote(mystrip(a['href'],'/=')).replace('_',' '))
				if not foundTag:
					if not anchors:
						continue
					a = anchors[0]
					yield Tag(category,urllib.parse.unquote(mystrip(a['href'],'/=')).replace('_',' '))
				break
		else:
			firstChild = li.contents
			if len(firstChild)==0: continue
			if firstChild is None: continue
			firstChild = str(firstChild[0]).strip()
			if firstChild.startswith('Source:'):
				try: yield Source(li.find('a')['href'])
				except TypeError: 
					yield Source(firstChild[len('Source: '):])
			elif firstChild.startswith('Rating:'):
				rating = firstChild[len('Rating: '):].lower()
				yield Tag('rating',rating)
			elif firstChild.startswith('Size:'):
				a = li.find('a')
				if a:
					gotImage = True
					print("Image",a['href'])
					yield Image(a['href'])
	if not gotImage:
		for a in doc.findAll('a'):
			if a.contents and a.contents[0].strip and a.contents[0].strip().lower() in ('download','original image','save this flash (right click and save)'):
				href = a.get('href')
				if not href: continue
				print("Image",href)
				yield Image(href)

toNum = re.compile('[^0-9]*[0-9]{2,}')

def normalize(ourl):
	url = urllib.parse.urlparse(ourl)
	m = toNum.match(url.path)
	if not m:
		return ourl
		#raise RuntimeError("Couldn't figure out {}".format(url))
	url = ('https', url.netloc, m.group(0), None, None, None)
	return urllib.parse.urlunparse(url)



