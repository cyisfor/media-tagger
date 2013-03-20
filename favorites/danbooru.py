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
    for li in doc.findAll('li'):
        klass = li.get('class')
        if klass and klass[0].startswith('tag-type-'):
            category = klass[0][len('tag-type-'):]
            for a in li.findAll('a'):
                if len(a.contents)>0:
                    if a.contents[0] == '?':
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
                gotImage = True
                yield Image(li.find('a')['href'])
    if not gotImage:
        for a in doc.findAll('a'):
            if a.contents and a.contents[0].strip() == 'Download' and 'href' in a:
                yield Image(a['href'])

toNum = re.compile('.*[0-9+]')

def normalize(url):
    m = toNum.match(url)
    if not m: raise RuntimeError("Couldn't figure out {}".format(url))
    return m.group(0)


