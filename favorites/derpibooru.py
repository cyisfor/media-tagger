from .things import *
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
    for taglist in doc.findAll('div',{'class': 'tagsauce'}):    
        for tag in taglist.findAll('span'):
            if not 'tag' in tag.get('class',()): continue
            namespace = tag.get('data-tag-namespace','general')
            try: name = tag['data-tag-name-in-namespace']
            except KeyError:
                print('tag is',tag)
                raise
            yield Tag(namespace,name)
    sauce = doc.find('span',{'class': 'source_url'})
    if sauce:
        yield Source(sauce.find('a')['href'])
    imgr = doc.find('div',id='image_target').next.next
    foundImage = False
    for a in doc.findAll('a'):
        rel = a.get('rel')
        if not rel:
            continue
        if 'nofollow' in rel and a.contents[0].strip and a.contents[0].strip().lower()=='download':
            href = a.get('href')
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
    path = urllib.parse.urlparse(url).path
    if path.startswith('/images/'):
        path = path[len('/images'):]
    url = urllib.parse.urlunparse(('https','derpibooru.org',path,None,None,None))
    #raise SystemExit('okay',url)
    return url
