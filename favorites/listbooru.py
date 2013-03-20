import setupurllib
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

def isThumb(a,img,src):
    if 'thumb' in src: return True
    klass = a.get('class')
    if klass and 'thumb' in klass: return True
    klass = img.get('class')
    if klass and ('thumb' in klass or 'preview' in klass): return True
    return False


def findLinks(base,doc,nextbox):
    for a in doc.findAll('a'):
        href = a.get('href')
        if not href: continue
        img = a.find('img')
        if not img:
            contents = a.contents[0]
            if '>>' in contents or 'next' in contents.lower():
                nextbox[0] = urllib.parse.urljoin(base,href)
            continue
        src = img.get('src')
        if not ( src and isThumb(a,img,src)): continue
        yield urllib.parse.urljoin(base,href)

def findPages(base):
    while True:
        with urllib.request.urlopen(base) as inp:
            doc = BeautifulSoup(inp)
        nextbox = [None]
        yield findLinks(base,doc,nextbox)
        if nextbox[0] is None: return
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
            sys.stdout.write(link+'\0')
            sys.stdout.flush()
