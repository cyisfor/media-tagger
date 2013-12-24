from .things import *
import re
import urllib.parse
import urllib.request
import setupurllib
from bs4 import BeautifulSoup

def mystrip(s,chars):
    for c in chars:
        i = s.rfind(c)
        if i >= 0:
            s = s[i+1:]
    return s

urldiv = re.compile('; *url=')

def deredirect(url):
    nextURL = None
    with urllib.request.urlopen(url) as inp:
        location = inp.headers.get('Location')
        if location:
            return deredirect(location)
        head = inp.read(0x1000)
        doc = BeautifulSoup(head)
        for meta in doc.findAll('meta'):
            eq = meta.get('http-equiv')
            if not ( eq and eq == 'refresh' ): continue
            content = meta.get('content')
            print(content)
            time,href = urldiv.split(content.lower())
            nextURL = urllib.parse.urljoin(url,href.strip('"\''))
            break
        if not nextURL:
            return inp.url
    return deredirect(nextURL)

def extract(doc):
    ul = doc.find('ul',{'id': 'tag-sidebar'})
    for li in ul.findAll('li'):
        category = li['class'][0][len('tag-type-'):]
        value = li.find('a').contents[0].strip()
        yield Tag(category,value)
    sidebar = ul.parent.parent
    stats =  sidebar.find('div',{'id': 'stats'})
    for li in stats.findAll('li'):
        key,rest = li.contents[0].split(':',1)
        key = key.strip()
        if key == 'Rating':
            yield Tag('rating',rest.strip().lower())
        elif key == 'Source':
            a = li.find('a')
            if a:
                href = a['href']
            else:
                href = rest
            if not 'adf.ly' in href:
                try:
                    yield Source(deredirect(href))
                except ValueError: pass
    options = stats.findNextSiblings('div')[0]
    for li in options.findAll('li'):
        a = li.find('a')
        if a and a.contents[0].strip()=='Original image':
            yield Image(a['href'])
