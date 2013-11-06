from things import *
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
    taglist = doc.find('div',{'class': 'tag-list'})
    for tag in taglist.findAll('a',rel="tag"):
        name = tag.contents[0].strip()
        if ':' in name:
            yield Tag(*name.split(':'))
        else:
            yield Tag('general',name)
    sauce = doc.find('span',{'class': 'source_url'})
    if sauce:
        yield Source(sauce.find('a')['href'])
    imgr = doc.find('div',id='image_target').next.next
    foundImage = False
    for a in doc.findAll('a'):
        rel = a.get('rel')
        if not rel:
            continue
        if 'nofollow' in rel and a.contents[0].strip().lower()=='download':
            href = a.get('href')
            print('FOU',href);
            yield Image(href)
            foundImage = True
    if not foundImage:
        for img in imgr.findAll('img'):
            src = img.get('src')
            if not src: continue
            if '/thumbs/' in src: continue
            yield Image(src)
            foundImage = True

noquery = re.compile('^[^?]*')

def normalize(url):
    m = noquery.match(url)
    if not m: raise RuntimeError("Couldn't figure out {}".format(url))
    return m.group(0)
