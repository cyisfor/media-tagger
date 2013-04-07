import create
import setupurllib
import db
import fixprint

from bs4 import BeautifulSoup
import urllib.parse
import urllib.request
from setupurllib import myretrieve

Request = urllib.request.Request

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
                doc = BeautifulSoup(doc)
                setattr(doc,'url',primarySource)
            sources = [primarySource]
            medias = []
            tags = [Tag('general',tag) for tag in handlers.get('tags',[])]
            for thing in handlers['extract'](doc):
                if isinstance(thing,Tag):
                    tags.append(thing)
                elif isinstance(thing,Media):
                    medias.append(thing)
                elif isinstance(thing,Source):
                    sources.append(thing)
            if not medias:
                print("No media. Failing...")
                continue
            if 'normalize' in handlers:
                primarySource = handlers['normalize'](primarySource)
            if True:
                print("tags",tags)
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
                name = urllib.parse.unquote(media.url.rsplit('/')[1])
                urllib.request._opener.addheaders.append(
                    ('Referer',primarySource))
                def download(dest):
                    myretrieve(Request(media.url,
                        headers=media.headers),
                        dest)
                    dest.seek(0,0)
                    mtime = os.fstat(dest.fileno()).st_mtime
                    return datetime.datetime.fromtimestamp(mtime)
                create.internet(download,media.url,tags,derpSource,derpSources)
            return
    print(url.netloc)
    raise RuntimeError("Can't parse {}!".format(primarySource))

def matchNetloc(s):
    def matcher(url):
        return url.netloc == s
    return matcher

def registerFinder(matcher,handler):
    if hasattr(matcher,'search'):
        temp = matcher
        matcher = lambda url: temp.search(url.netloc)
    elif callable(matcher): pass
    else:
        matcher = matchNetloc(matcher)
    finders.append((matcher,handler))

def alreadyHere(uri):
    result = db.c.execute("SELECT id FROM urisources WHERE uri = $1",(uri,))
    if len(result)==0: return False
    return True
