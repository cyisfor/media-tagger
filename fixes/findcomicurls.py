import comicPool
import setupurllib
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import db

def checkIt(link):
    with urllib.request.urlopen(link) as inp:
        doc = BeautifulSoup(inp)
    for a in doc.findAll('a'):
        if not a: continue
        if isinstance(a,str): continue
        try: href = a.get('href')
        except:
            print(type(a),a)
        if not href: continue
        if not 'pool/show' in href: continue
        return urllib.parse.urljoin(link,href)
    return False

for comic,title in db.execute('SELECT id,title FROM comics WHERE source IS NULL'):
    print(title)
    for link, in db.execute("SELECT uri FROM urisources WHERE ARRAY[id] <@ ANY(SELECT sources FROM media WHERE id IN (SELECT medium FROM comicpage WHERE comic = $1))",(comic,)):
        print('whee',link)
        if 'post/show' in link:
            pool = checkIt(link)
            if not pool: continue
            print('got pool',pool)
            comicPool.getPool(pool)
            break
    else:
        print('no pool found')

