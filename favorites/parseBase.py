import create
import setupurllib
import db
import fixprint

from bs4 import BeautifulSoup
import urllib.parse
import urllib.request
from setupurllib import myretrieve
import tempfile
import shutil

Request = urllib.request.Request

import os
import datetime

try: from .things import *
except SystemError:
    from things import *

finders = []

skip = os.environ.get('skip')

def parse(primarySource):
    if skip and db.execute("SELECT id FROM urisources WHERE uri = $1",(primarySource,)):
        print('skipping',primarySource)
        return
    print('parsing',repr(primarySource))
    url = urllib.parse.urlparse(primarySource)
    doc = None
    for name,matcher,handlers in finders:
        if matcher(url):
            if 'normalize' in handlers:
                primarySource = handlers['normalize'](primarySource)
            with tempfile.NamedTemporaryFile() as temp:
                headers = myretrieve(urllib.request.Request(primarySource),temp)
                temp.seek(0,0)
                inp = temp
                
                if not headers.get('Content-Type').startswith('text/html'):
                    raise RuntimeError(primarySource,"not html")
                doc = inp.read()
                doc = BeautifulSoup(doc)
                setattr(doc,'url',primarySource)
            medias = []
            def generalize(tag):
                if isinstance(tag,Tag): return tag
                try:
                    if len(tag) == 2:
                        if len(tag[0]) >= 3 and len(tag[1]) >= 3:
                            return Tag(*tag)
                except TypeError: pass
                if ':' in tag:
                    return Tag(*(tag.split(':')))
                return Tag('general',tag)
            tags = [generalize(tag) for tag in handlers.get('tags',[])]
            if skip and db.execute("SELECT id FROM urisources WHERE uri = $1",(primarySource,)):
                print('skipping',primarySource)
                return
            sources = [primarySource]
            name = None
            for thing in handlers['extract'](doc):
                if isinstance(thing,Tag):
                    tags.append(thing)
                elif isinstance(thing,Media):
                    medias.append(thing)
                elif isinstance(thing,Source):
                    sources.append(thing)
                elif isinstance(thing,Name):
                    name = thing
            if not medias:
                print(name,primarySource,"No media. Failing...")
                continue
            if True:
                print("tags",[str(tag) for tag in tags])
                print("name",repr(name))
                print("Media",len(medias))
                print("PSource",primarySource)
                print("Sources",sources)
            for media in medias:
                derpSources = sources + [media.url]
                media.url = urllib.parse.urljoin(primarySource,media.url)
                if len(medias) == 1:
                    derpSource = primarySource
                else:
                    derpSource = media.url
                derpSources = [urllib.parse.urljoin(primarySource,source) for source in derpSources]
                media.headers['Referer'] = primarySource
                def download(dest):
                    myretrieve(Request(media.url,
                        headers=media.headers),
                        dest)
                    dest.seek(0,0)
                    mtime = os.fstat(dest.fileno()).st_mtime
#                    with open('/tmp/derp.image','wb') as out:
#                        shutil.copyfileobj(dest,out)
                    dest.seek(0,0)
                    return datetime.datetime.fromtimestamp(mtime)
#                def download(dest):
#                    with open('/tmp/derp.image','rb') as inp:
#                        shutil.copyfileobj(inp,dest)
#                        mtime = os.fstat(inp.fileno()).st_mtime
#                    return datetime.datetime.fromtimestamp(mtime)
                try:
                    image,wasCreated = create.internet(download,media.url,tags,derpSource,derpSources,
                        name = name)
                    return image
                except create.NoGood:
                    print("No good",media.url,media.headers)
                    raise
            return
    raise ParseError("Can't parse {}!".format(primarySource))

def normalize(url):
    burl = urllib.parse.urlparse(url)
    for name,matcher,handlers in finders:
        if matcher(burl):
            if 'normalize' in handlers:
                return handlers['normalize'](url)
            return url
    return url

class ParseError(RuntimeError): pass

def matchNetloc(s):
    def matcher(url):
        return url.netloc.endswith(s)
    return matcher

def registerFinder(matcher,handler,name=None):
    if name is None: name = matcher
    if hasattr(matcher,'search'):
        temp = matcher
        matcher = lambda url: temp.search(url.netloc)
    elif callable(matcher): pass
    else:
        matcher = matchNetloc(matcher)
    finders.append((name,matcher,handler))

def alreadyHere(uri):
    result = db.execute("SELECT id FROM urisources WHERE uri = $1",(uri,))
    if len(result)==0: return False
    return True
