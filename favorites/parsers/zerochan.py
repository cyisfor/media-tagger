from favorites.things import *
from favorites.parse import ParseError
import re
import urllib.parse

def mystrip(s,chars):
	for c in chars:
		i = s.rfind(c)
		if i >= 0:
			s = s[i+1:]
	return s

def extract(doc):
	gotImage = False
	for img in doc.findAll('img'):
		title = img.get('title')
		if title:
			if title.startswith('View full size'):
				gotImage = True
				yield Image(img.parent['href'])
			elif title.startswith("No larger size available"):
				gotImage = True
				yield Image(img['src'])
	if not gotImage:
		raise ParseError("no image because we don't care")
	tags = doc.find('ul',id='tags').findAll('li')
	for li in tags:
		contents = list(li.contents)
		if len(contents)==2:
			name,category = contents
			category = category.strip()
			if not category:
				category = None
			name = name.contents[0]
		else:
			category = None
			name = contents[0].contents[0]
		yield Tag(category,name)
