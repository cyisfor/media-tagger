#!/usr/bin/python3

import create,withtags

import setupurllib

from bs4 import BeautifulSoup

import urllib.request
from urllib.request import Request
import datetime
import os

implied = set()
for tag in os.environ['tags'].split(','):
    tag = tag.strip()
    implied.add(tag)

def mysplit(s,cs):
    pending = ''
    for c in s:
        if c in cs:
            if pending:
                try: int(pending)
                except ValueError as e:
                    # only yield if NOT an integer
                    yield pending
            pending = ''
        else:
            pending += c
    if pending:
        try: int(pending)
        except ValueError as e:
            yield pending

boring = set(["the","for","this","and","not","how","are","files","xcf","not","my","in"])

def copyMe(source):
    def download(dest):
        shutil.copy2(source,dest.name)
        return datetime.datetime.fromtimestamp(os.fstat(dest.fileno()).st_mtime)
    return download

top = os.environ['url']
with urllib.request.urlopen(top) as inp:
    doc = BeautifulSoup(inp)

memory = set()

for i,link in enumerate(doc.findAll('a')):
    href = link.get('href')
    if not href: continue
    if href.startswith('javascript:'): continue
    if href.startswith('about:'): continue
    if '#' in href: continue
    ext = href[-3:].lower()
    if not (ext == 'jpg' or ext == 'png'): continue
    if href in memory: continue
    memory.add(href)
    print(href)    
    relpath = urllib.parse.urlparse(href).path
    discovered = tuple(mysplit(relpath[:relpath.rfind('.')].lower(),'/ .-_*"\'?()[]{},'))
    discovered = set([comp for comp in discovered if len(comp)>2 and comp not in boring])
    def download(dest):
        setupurllib.myretrieve(Request(href,headers={'Referer': top}),dest)
        dest.seek(0,0)
        mtime = os.fstat(dest.fileno()).st_mtime
        return datetime.datetime.fromtimestamp(mtime)
    ID = create.internet(download,href,implied.union(discovered),href,())
    print(hex(ID))
    # then insert into a pool named by unique ID ????
