from favorites.things import *
from favorites.parse import ParseError
import re
import urllib.parse

def hasClass(c):
    def handler(e):
        return e == c
    return handler


def extract(doc):
    image = False
    for a in doc.findAll('a'):
        href = a.get('href')
        if not href: continue
        href = urllib.parse.urlparse(href).path
        try: name,category,rest = href[1:].split('/',2)
        except ValueError: continue
        if not category in set(("submissions","characters")):
            continue
        derp = href.rsplit('.',1)
        if len(derp) == 2:
            ext = derp[1]
        else:
            # ehhhhhh
            ext = 'jpg'
        img = a.find('img')
        if img:
            name = img['alt'] + '.' + ext
            print('found',href,name)
            yield Name(name)
            yield Image(href)
            image = True
    if not image:
        raise ParseError("Couldn't find image")
    div = doc.find('div',{'class': lambda e: e and 'tags' in e})
    tags = False
    for a in div.findAll('a'):
        href = a.get('href')
        if not href: continue
        if not str(href).startswith('/search?q='): continue
        yield Tag(None,urllib.parse.unquote(href[len('/search?q='):]))
        tags = True
    if not tags:
        raise Exception("No tags found")
    header = doc.find('h1',id='detail-title')
    artist = header.find('a',{'class': 'username'}).contents[0]
    yield Tag('artist',artist)
