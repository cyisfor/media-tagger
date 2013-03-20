import create
import setupurllib
import db

from bs4 import BeautifulSoup
import urllib.parse
import urllib.request

import os
import datetime

from things import *

finders = []

def parse(primarySource):
    url = urllib.parse.urlparse(primarySource)
    for matcher,handlers in finders:
        if matcher(url):
            with urllib.request.urlopen(primarySource) as inp:
                doc = inp.read()
                if 'gzip' in inp.headers.get('Content-encoding',''):
                    import gzip
                    doc = gzip.decompress(doc)
            sources = [primarySource]
            image = None
            tags = [Tag('general',tag) for tag in handlers.get('tags',[])]
            for thing in handlers['extract'](BeautifulSoup(doc)):
                if isinstance(thing,Tag):
                    tags.append(thing)
                elif isinstance(thing,Image):
                    sources.append(thing)
                    image = thing
                elif isinstance(thing,Source):
                    sources.append(thing)
            if not image:
                print("No image. Failing...")
                continue
            if 'normalize' in handlers:
                primarySource = handlers['normalize'](primarySource)
            image = urllib.parse.urljoin(primarySource,image)
            sources = [urllib.parse.urljoin(primarySource,source) for source in sources]
            if False:
                print("tags",tags)
                print("Image",image)
                print("PSource",primarySource)
                print("Sources",sources)
            name = urllib.parse.unquote(image.rsplit('/')[1])
            urllib.request._opener.addheaders.append(
                    ('Referer',primarySource))
            def download(dest):
                urllib.request.urlretrieve(image,dest.name)
                dest.seek(0,0)
                mtime = os.fstat(dest.fileno()).st_mtime
                return datetime.datetime.fromtimestamp(mtime)
            create.internet(download,image,tags,primarySource,sources)
            return
    raise RuntimeError("Can't parse {}!".format(primarySource))

def registerFinder(matcher,handler):
    if hasattr(matcher,'search'):
        temp = matcher
        matcher = lambda url: temp.search(url.netloc)
    elif callable(matcher): pass
    else:
        temp = matcher
        matcher = lambda url: url.netloc == temp
    finders.append((matcher,handler))

def alreadyHere(uri):
    result = db.c.execute("SELECT id FROM urisources WHERE uri = $1",(uri,))
    if len(result)==0: return False
    return True
