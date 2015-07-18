from .things import *
import re
import urllib.parse

def mystrip(s,chars):
    for c in chars:
        i = s.rfind(c)
        if i >= 0:
            s = s[i+1:]
    return s

notags = re.compile('([0-9]+).*(\\..*)')

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
        imgr = doc.find('div',id='image_target')
        yield Image(imgr.getAttribute('data-download-uri'))

def normalize(url):
    u = urllib.parse.urlparse(url)
    host = u.netloc
    path = u.path
    if host == 'derpiboo.ru':
        host = 'derpibooru.org'
    elif host.endswith('derpicdn.net'):
        path,tail = path.rsplit('/',1)
        match = notags.match(tail)
        if match:
            path = path + '/' +  match.group(1) + match.group(2)
    elif not host.endswith('derpibooru.org'):
        return url

    if path.startswith('/images/'):
        path = path[len('/images'):]
    url = urllib.parse.urlunparse(('https',host,path,None,None,None))
    #raise SystemExit('okay',url)
    return url
