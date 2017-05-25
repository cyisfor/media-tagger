from favorites.things import *
import note

import re
import urllib.parse

def extract(doc):
	if '///files' in doc.url: return

	kwdiv = None
	for div in doc.findAll('div'):
		contents = div.contents
		if not contents: continue
		contents = str(contents[0]).strip()
		if contents=='Keywords':
			kwdiv = div.parent
			break
	else:
		print(str(doc))
		return
	for a in kwdiv.findAll('a'):
		href = a.get('href')
		if not href: continue
		if not 'keyword' in href: continue
		if 'blockkeywords' in href: continue
		span = a.find('span')
		if not span:
			print(str(a))
			raise SystemExit
		keyword = str(span.contents[0]).strip()
		yield Tag(None,keyword)
	foundImage = False
	contentdiv = doc.find('div',{ 'id': 'size_container' })
	for a in contentdiv.findAll('a'):
		href = a.get('href')
		if not href: continue
		for span in a.findAll('span'):
			contents = str(span.contents[0]).strip().lower()
			if 'download' in contents:
				foundImage = True
				note.alarm("yaaaay",href)
				yield Image(href)
				break
		else:
			continue
		break
	if foundImage: return
	image = None
	maxSize = None
	for img in doc.findAll('img'):
		if img:
			if not ( img.get('width') and img.get('height') ):
				continue
			size = float(img.get('width')) * float(img.get('height'))
			src = img.get('src')
			if maxSize is None or size > maxSize:
				print(img.get('width'),img.get('height'))
				print(src)
				print(maxSize,"->",size)
				maxSize = size
				image = src
	if image:
		foundImage = True
		print(image)
		yield Image(image)
