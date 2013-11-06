from things import *
import re
import urllib.parse

def extract(doc):
    if '///files' in doc.url: return
    kwdiv = None
    for div in doc.findAll('div'):
        if div.contents and str(div.contents[0]).strip()=='Keywords':
            kwdiv = div.parent
    if kwdiv is None:
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
        yield Tag('general',keyword)
    foundImage = False
    contentdiv = doc.find('div',{ 'id': 'size_container' })
    for a in contentdiv.findAll('a'):
        if not a.contents: continue
        span = a.find('span')
        if span:
            if str(span.contents[0]).strip() in {'max. preview','download'}:
                href = a.get('href')
                if not href: continue
                foundImage = True
                yield Image(href)
    if not foundImage:
        image = None
        maxSize = None
        for img in doc.findAll('img'):
            if img:
                if not ( img.get('width') and img.get('height') ):
                    continue
                size = int(img.get('width')) * int(img.get('height'))
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
