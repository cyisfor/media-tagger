from ..parse import ParseError
from .things import *
import re
import urllib.parse

def mystrip(s,chars):
    for c in chars:
        i = s.rfind(c)
        if i >= 0:
            s = s[i+1:]
    return s

kwMatch = re.compile('/search/@keywords (.*)')

def extract(doc):
    linx = doc.find('div',id='keywords')
    if linx:
        for a in linx.findAll('a'):
            href = a.get('href')
            if not href: continue
            m = kwMatch.match(href)
            if not m: continue
            yield Tag(None,m.group(1).lower())
    auth = doc.findAll('td',{'class':'cat'})
    if not auth or len(auth) < 2:
        raise ParseError("No author on furaffinity?")
    auth = auth[1]
    for a in auth.findAll('a'):
        href = a.get('href')
        if not href: continue
        if not href.startswith('/user/'): continue
        yield Tag('artist',href[len('/user/'):].rstrip('/'))
    for a in doc.findAll('a'):
        if not a.contents: continue
        if not 'Download' == str(a.contents[0]).strip(): continue
        href = a.get('href')
        if not href: continue
        yield Image(href)
def normalize(url):
    return url.replace('/full/','/view/')
