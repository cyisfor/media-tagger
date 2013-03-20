import setupurllib
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

def isThumb(a,img,src):
    if 't.facdn.net' in src: return True
    return False

def findLinks(base,doc,nextbox):
    pieces = base.rsplit('/',2)
    if len(pieces)==3:
        try: nextbox[0] = '../'+str(int(pieces[1])+1)+'/'
        except ValueError: pass
    if not nextbox[0]:
        nextbox[0] = '2/'
    nextbox[0] = urllib.parse.urljoin(base,nextbox[0])
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
