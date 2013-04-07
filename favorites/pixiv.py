from things import *
import re
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
from contextlib import closing

import re

findImage = re.escape("pixiv.context.images[")+'[0-9]+'+re.escape("].unshift('")+"([^\\']+)"+re.escape("')")
findImage = re.compile(findImage)

def testFindImage():
    for image in findImage.finditer("aoeu aoeu aoeupixiv.context.images[0].unshift('http://i1.pixiv.net/img45/img/daga2626/28862993_p0.png') aoeustnh nsahte unsaheu pixiv.context.images[0].unshift('http://i1.pixiv.net/img45/img/daga2626/28862993_p0.png') derrrrp pixiv.context.images[0].unshift('http://i1.pixiv.net/img45/img/daga2626/28862993_p0.png') aoeu aoeu aoeu"):
        print(image.group(1))

def extract(doc):
    isManga = doc.find('div',{'class':'works_display'})
    if isManga:
        isManga = isManga.find('a')
        if isManga:
            isManga = isManga.get('href')
            if isManga:
                isManga = 'manga' in isManga
    idu = doc.url.replace('medium','manga' if isManga else 'big')
    with closing(urllib.request.urlopen(urllib.request.Request(
        idu,
        headers={'Referer':doc.url}))) as inp:
            if isManga:
                images = findImage.findall(inp.read().decode('utf-8'))
            else:
                imgdoc = BeautifulSoup(inp.read())
    foundImage = False
    if isManga:
        for image in images:
            foundImage = True
            yield Image(image,{'Referer':idu})
    else:
        img = imgdoc.find('img')
        yield Image(img['src'],{'Referer':idu})
        foundImage = True
    if foundImage is False:
        raise Exception("No image!")
    artist = doc.find('h1',{'class': 'user'})
    if not artist:
        raise Exception("no artist?")
    yield Tag('artist',artist.contents[0].strip())
    for a in doc.findAll('a'):
        href = a.get('href')
        if not href: continue
        tageq = href.find('tag=')
        if tageq > 0:
            yield Tag('general',
                    urllib.parse.unquote(href[tageq+4:]))
