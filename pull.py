import tags as tagsModule
import create
from setupurllib import myretrieve,myopen

from bs4 import BeautifulSoup

from pprint import pprint
import dateutil.parser
import urllib.parse as up

def pull(url):
    purl = up.urlparse(url)
    def newpath(path):
        return up.urlunparse((purl.scheme,purl.netloc,path,purl.params,purl.query,purl.fragment))
    try:
        art,page,ident = purl.path.rstrip('/').rsplit('/',2)
        ident = int(ident,0x10)
    except ValueError: 
        print('er',purl.path)
        return False
    base = art.rsplit('/',1)[0]

    info = newpath(art+'/~info/{:x}/'.format(ident))
    print(info)
    with myopen(info) as inp:
        doc = BeautifulSoup(inp)
    sources = [a['href'] for a in doc.find(id='sources').findAll('a')]
    name = doc.find(id='name').contents[0]
    created = dateutil.parser.parse(doc.find(id='created').contents[0])
    tags = tagsModule.parse(doc.find(id='tags').contents[0])
    filetype = doc.find(id='type').contents[0]

    media = newpath(base+'/image/{:x}/{}/{}'.format(ident,filetype,name))

    def download(dest):
        myretrieve(Request(media,
            headers={'Referer': url}),
            dest)
        return created

    return create.internet(download,media,tags,sources[0] if sources else url,sources,name=name)

if __name__ == '__main__':
    ident = pull(input('URL of picture page: '))
    if ident:
        print('Got it!',ident)
    else:
        print('Pull failed...')
