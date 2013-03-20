from things import *
import re
import urllib.parse

def extract(doc):
    for div in doc.findAll('div'):
        if div.contents and str(div.contents[0]).strip()=='Keywords':
            kwdiv = div.parent
    for a in kwdiv.findAll('a'):
        href = a.get('href')
        if not href: continue
        if not 'keyword' in href: continue
        if 'blockkeywords' in href: continue
        span = a.find('span')
        if not span:
            print(str(a))
            raise SystemExit
        keyword = str(span.contents[0]).strip()
        yield Tag('general',keyword)
    contentdiv = doc.find('div',{ 'id': 'size_container' })
    for a in contentdiv.findAll('a'):
        if not a.contents: continue
        span = a.find('span')
        if not span: continue
        if str(span.contents[0]).strip() != 'max. preview': continue
        href = a.get('href')
        if not href: continue
        yield Image(href)
