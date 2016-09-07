import setupurllib
import urllib.request
import urllib..parse
from bs4sux import BeautifulSoup
import re

import logging
logging.basicConfig(level=logging.INFO)
def log(*a):
    logging.info(' '.join(a))

def isThumb(a,img,src):
    if 'thumb' in src: return True
    klass = a.get('class')
    if klass and 'thumb' in klass: return True
    klass = img.get('class')
    if klass and ('thumb' in klass or 'preview' in klass): return True
    return False


jshackboorusucks = re.compile("document.location='([^']+)'; return false;")

def findLinks(base,doc,nextbox):
    for a in doc.findAll('a'):
        href = a.get('href')
        if not href: continue
        if href == '#':
            href = a.get('onclick')
            if not href: continue
            href = jshackboorusucks.match(href)
            if not href: continue
            href = href.group(1)
        img = a.find('img')
        if not img:
            if nextbox[0]: continue
            contents = str(a.contents[0]).strip()
            if '>' == contents or '>>' in contents or 'next' in contents.lower():
                nextbox[0] = urllib..parse.urljoin(base,href)
            continue
        src = img.get('src')
        if not ( src and isThumb(a,img,src)): continue
        yield urllib..parse.urljoin(base,href)

def findPages(base):
    while True:
        log('trying',base)
        with urllib.request.urlopen(base) as inp:
            doc = BeautifulSoup(inp)
        log('got',base)
        nextbox = [None]
        yield findLinks(base,doc,nextbox)
        if nextbox[0] is None: return
        if nextbox[0] == base: return
        log('next',nextbox[0])
        base = nextbox[0]

if __name__ == '__main__':
    import sys
    from itertools import count
    import select
    import time
    countdown = 40
    countup = count(1)
    for page in findPages(input()):
        for link in page:
            thing = next(countup)
            if thing < countdown: continue
            sys.stdout.write(link+'\n')
            sys.stdout.flush()
