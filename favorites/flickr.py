from .things import Image,Tag,Source
import os
import re
from contextlib import closing
from bs4sux import BeautifulSoup

import urllib.request
import urllib.parse

here = os.path.dirname(__file__)
with open(os.path.join(here,"flickr.api"),"rt") as inp:
    apiKey = inp.read().rstrip()

def getLargest(id):
    with closing(urllib.request.urlopen("http://api.flickr.com/services/rest/?method=flickr.photos.getSizes&api_key={}&photo_id={}".format(apiKey,id))) as inp:
        doc = BeautifulSoup(inp)
    src = None
    maxWidth = None
    for size in doc.findAll('size'):
        width = size.get('width')
        if not width: continue
        width = int(width)
        print(width)
        if not maxWidth or width > maxWidth:
            print("width",width)
            maxWidth = width
            src = size['source']
    assert src is not None
    return src

photoID = re.compile("photo_id *= *\\'([0-9a-f]+)\\';")

def extract(doc):
    foundImage = False
    for script in doc.findAll('script'):
        thing = ''.join(script.contents)
        m = photoID.search(thing)
        if m:
            foundImage = True
            sneaky = getLargest(m.group(1))
            yield Image(sneaky)
            yield Source(sneaky)
            break
    assert foundImage
    tags = doc.find('ul',id='thetags')
    if tags:
        for tag in tags.findAll('a'):
            tag = tag['data-tag']
            if not tag: continue
            yield Tag(None,urllib.parse.unquote(tag))
    else:
        yield Tag('special','tagme')
