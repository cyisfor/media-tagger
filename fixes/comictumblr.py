import setupurllib
import create
import db

from bs4 import BeautifulSoup

import urllib.request

import re

geturl = re.compile('a *href="(https?://[^"]+)"')

for id,description in db.c.execute("SELECT id,description FROM comics WHERE description LIKE '<%a%href%http://%>' AND source IS NULL"):
    m = geturl.search(description)
    if not m:
        print('skipping',description)
        continue
    uri = m.group(1)
    with urllib.request.urlopen(uri) as inp:
        doc = BeautifulSoup(inp)
    title = doc.find('title')
    if not title:
        print('no title???',description)
        continue
    title = title.string
    if not title: continue
    with db.transaction():
        source = create.sourceId(uri)
    print('snornagling',uri,title)
    db.c.execute('UPDATE comics SET description = $1, source = $2 WHERE id = $3',(title,source,id))

