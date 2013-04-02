from things import *
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
        if not href.startswith("/static/submission/"): continue
        yield Image(href)
        image = True
    if not image:
        raise Exception("Couldn't find image")
    div = doc.find('div',{'class': lambda e: e and 'tags' in e})
    tags = False
    for a in div.findAll('a'):
        href = a.get('href')
        if not href: continue
        if not str(href).startswith('/search?q='): continue
        yield Tag('general',urllib.parse.unquote(href[len('/search?q='):]))
        tags = True
    if not tags:
        raise Exception("No tags found")
    header = doc.find('h1',id='detail-title')
    artist = header.find('a',{'class': 'username'}).contents[0]
    yield Tag('artist',artist)
