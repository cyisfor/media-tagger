import setupurllib
import urllib.request
import urllib.parse
from bs4sux import BeautifulSoup

import re

def isThumb(a,img,src):
    if 'thumbnails' in src: return True
    return False

findPage = re.compile('page=([0-9]+)')

def findLinks(base,doc,nextbox):
    m = findPage.search(base)
    assert(m)
    nex = int(m.group(1))+1
    nextbox[0] = findPage.sub(base,'page='+str(nex))
    for a in doc.findAll('a'):
        href = a.get('href')
        if not href: continue
        img = a.find('img')
        if not img: continue
        src = img.get('src')
        if not ( src and isThumb(a,img,src)): continue
        yield urllib.parse.urljoin(base,href)

def findPages(base):
    while True:
        try:
            with urllib.request.urlopen(base) as inp:
                doc = BeautifulSoup(inp)
        except urllib.error.HTTPError as e:
            print(base)
            print(dir(e))
            raise SystemExit
        nextbox = [None]
        yield findLinks(base,doc,nextbox)
        if nextbox[0] is None: return
        base = nextbox[0]

if __name__ == '__main__':
    import sys
    from itertools import count
    import select
    import time
    countdown = 0
    countup = count(1)
    for page in findPages(input()):
        for link in page:
            thing = next(countup)
            if thing < countdown: continue
            sys.stdout.write(link+'\0')
            sys.stdout.flush()
