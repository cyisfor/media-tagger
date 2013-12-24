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
    for li in doc.findAll('li'):
        klass = li.get('class')
        if klass and klass[0].startswith('tag-type-'):
            foundTag = False
            category = klass[0][len('tag-type-'):]
            anchors = li.findAll('a')
            for a in anchors:
                if len(a.contents)>0:
                    if a.contents[0] == '?':
                        foundTag = True
                        yield Tag(category,urllib.parse.unquote(mystrip(a['href'],'/=')).replace('_',' '))
            if not foundTag:
                a = anchors[0]
                yield Tag(category,urllib.parse.unquote(mystrip(a['href'],'/=')).replace('_',' '))
        else:
            firstChild = li.contents
            if len(firstChild)==0: continue
            if firstChild is None: continue
            firstChild = str(firstChild[0])
            if firstChild.startswith('Source:'):
                try: yield Source(li.find('a')['href'])
                except TypeError: pass
            elif firstChild.startswith('Rating: '):
                rating = firstChild[len('Rating: '):].lower()
                yield Tag('rating',rating)
            elif firstChild.startswith('Size: '):
                a = li.find('a')
                if a:
                    gotImage = True
                    print("Image",a['href'])
                    yield Image(a['href'])
    if not gotImage:
        for a in doc.findAll('a'):
            if a.contents and a.contents[0].strip and a.contents[0].strip().lower() in ('download','original image','save this flash (right click and save)'):
                href = a.get('href')
                if not href: continue
                print("Image",href)
                yield Image(href)

toNum = re.compile('.*[0-9+]')

def normalize(url):
    m = toNum.match(url)
    if not m: raise RuntimeError("Couldn't figure out {}".format(url))
    print(url,'normalized to',m.group(0))
    return m.group(0)


