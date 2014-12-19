import process
import note
import json

from place import place
from itertools import count
import fixprint

from dimensions import thumbnailPageSize,thumbnailRowSize

import comic
from user import User,dtags as defaultTags
from session import Session
import tags
import context
from db import c
from redirect import Redirect
import filedb

import json
from urllib.parse import quote as derp, urljoin
import time
import datetime

import textwrap

maxWidth = 800
maxSize = 0x40000

def quote(s):
    try:
        return derp(s).replace('/','%2f')
    except:
        print(repr(s))
        raise

def makeLinks(info):
    allexists = True
    def iter():
        nonlocal allexists
        for id,name,type,tagz in info:
            tagz = [str(tag) for tag in tagz]
            fid,oneexists = filedb.check(id,create=False)
            allexists = allexists and oneexists
            yield dict(id=id,exists=oneexists,name=name,type=type,tags=tags.full(tagz))
    return {'allexists': allexists, 
            'rowsize': thumbnailRowSize, 
            'links': iter()}

def makeBase():
    # drop bass
    return 'http://[fcd9:e703:498e:5d07:e5fc:d525:80a6:a51c]/art/'

@context.Context
class Links:
    next = None
    prev = None
    id = None

def standardHead():
    ret = {}
    if Links.prev is not None:
        ret['prev'] = Links.prev
    if Links.next is not None:
        ret['next'] = Links.next
    if Links.id is not None:
        ret['id'] = Links.id
    return ret

def makePage(content=None,**kw):
    ret = standardHead()
    if content:
        ret.update(content)
    ret.update(kw)
    return ret

def makeLink(id,type,name,doScale,width=None,height=None):
    if doScale:
        if not type.startswith('image'):
            doScale = False
    if doScale: # still...
        fid,exists = filedb.checkResized(id,create=False)
    else:
        fid,exists = filedb.check(id,category='media',create=False)

    ret = dict(id=id,exists=exists,type=type,name=name,resized=(doScale is True))
    if width:
        ret['width'] = width
    if height:
        ret['height'] = height
    return ret

def simple(info,path,params):
    if Session.head: return
    return info

def resized(info,path,params):
    id = int(path[1],0x10)
    return dict(zip(('fid','exists'),filedb.checkResized(id)))

def page(info,path,params):
    if Session.head:
        id,modified,size = info
    else:
        id,next,prev,name,type,width,height,size,modified,tags,comic = info

    doScale = User.rescaleImages and size >= maxSize

    if Session.head:
        if doScale: 
            fid, exists = filedb.checkResized(id)
            Session.refresh = not exists and type.startswith('image')
        Session.modified = modified
        return
    with Links:
        Links.id = id
        Session.modified = modified
        if name:
            name = quote(name)
            if not '.' in name:
                name = name + '/untitled.jpg'
        else:
            name = 'untitled.jpg'
        # assume tags are (category,name) or just name in general:
        link = makeLink(id,type,name,doScale,width,height)
        # comic, title, prev, next = comic
        if next:
            Links.next = next
        if prev:
            Links.prev = prev
        link['tags'] = tags
        return makePage(link)

def info(info,path,params):
    Session.modified = info['sessmodified']
    del info['sessmodified']
    with Links:
        sources = info.pop('sources')
        if sources is None:
            sources = ()
        else:
            import info as derp
            sources = ((id,derp.source(id)) for id in sources)
            sources = [pair for pair in sources if pair[1]] # no empty URLs
        info['sources'] = sources
        Links.id = info.pop('id')
        fid,exists = filedb.check(Links.id)
        Session.refresh = not exists
        if Session.head: return        
    return makePage(info)

def media(url,query,offset,info,related,basic):
    #related = tags.names(related) should already be done
    import sys,os
    with Links:
        info = list(info)
        if len(info)>=thumbnailPageSize:
            Links.next = offset + 1
        if offset > 0:
            Links.prev = offset - 1
        if Session.head:
            return
        related = tags.full(related)
        basic = tags.full(basic)

        return makePage(
                tags=basic,
                links=makeLinks(info))

def desktop(raw,path,params):
    import desktop
    if 'n' in params:
        n = int(params['n'][0],0x10)
    else:
        n = 1
    history = desktop.history(n)
    if not history:
        return dict(error="No desktops yet!?")
    current = history[0]
    history = history[1:]
    id,name,modified,type,tags,tagnames = c.execute("SELECT media.id,name,modified,type,array(select id from tags where tags.id = ANY(neighbors)),array(select name from tags where tags.id = ANY(neighbors)) FROM media INNER JOIN things ON things.id = media.id WHERE media.id = $1",(current,))[0]
    Session.etag = 'desktop-'+str(id)+str(modified) 
    # can't do Session.modified b/c old pictures might show up newly
    def makeDesktopLinks():
        allexists = True
        for id,name in c.execute("SELECT id,name FROM media WHERE id = ANY ($1::bigint[])",(history,)):
            fid,exists = filedb.check(id) 
            allexists = allexists and exists
            yield dict(id=id,name=name,exists=exists)
        Session.refresh = not allexists
    info = dict(current=current,name=name,modified=modified,tags=zip(tags,tagnames),type=type)
    if history:
        info['history'] = tuple(makeDesktopLinks())
    if Session.head: return
    return makePage(info)

def user(info,path,params):
    if Session.head: return
    return dict(useDefault=User.defaultTags,rescale=User.rescaleImages, implied=tags.full(User.impliedTags))

def getPage(params):
    page = params.get('p')
    if not page:
        return 0
    else:
        return int(page[0])

def getType(medium):
    return c.execute("SELECT type FROM media WHERE id = $1",(medium,))[0][0]

def getStuff(medium):
    return c.execute('''SELECT 
    type,
    size,
    COALESCE(images.width,videos.width),
    COALESCE(images.height,videos.height)
    FROM media 
    LEFT OUTER JOIN images ON media.id = images.id 
    LEFT OUTER JOIN videos ON media.id = videos.id 
    WHERE media.id = $1''',(medium,))[0]

def comicPageLink(com,isDown=False):
    def pageLink(medium=None,counter=None):
        if isDown:
            link = ''
        else:
            link = '../'
        link = link + '{:x}/'.format(com)
        return link + unparseQuery()
    return pageLink

def comicNoExist():
    raise RuntimeError("Comic no exist")

def checkModified(medium):
    modified = c.execute('SELECT EXTRACT(EPOCH FROM modified) FROM media WHERE id = $1',(medium,))[0][0]
    if modified:
        if Session.modified:
            Session.modified = max(modified,Session.modified)
        else:
            Session.modified = modified

def showAllComics(params):
    page = getPage(params)
    comics = comic.list(page)
    def getInfos():
        for id,title in comics:
            try: 
                medium = comic.findMedium(id,0)
            except Redirect: 
                medium = 0x5c911
            if not medium: 
                medium = 0x5c911
            checkModified(medium)
            yield dict(id=id,medium=medium,title=title,type=getType(medium))
    if Session.head:
        for stuff in getInfos(): pass
        return
    return dict(total=comic.numComics(),
            page=page,
            comics=getInfos())

def showPages(path,params):
    com = int(path[0],0x10)
    page = getPage(params)
    numPages = comic.pages(com)
    offset = page * 0x20
    if offset and offset < numPages:
        def getMedia():
            for which in range(offset,min(0x20+offset,numPages)):
                medium = comic.findMedium(com,which)
                checkModified(medium)
                yield medium,which
    else:
        def getMedia(): 
            return ()

    if Session.head:
        for stuff in getMedia(): pass
        return
    title,description,source = comic.findInfo(com,comicNoExist)
    if not description: description = 'ehunno' 
    with Links:
        if page > 0:
            Links.prev = page - 1
        if page + 1 < numPages:
            Links.next = page + 1
        return makePage(
            comic=com,
            title=title,
            description=description,
            source=source,
            pages=numPages,
            media=getMedia())

def showComicPage(path):
    com = int(path[0],0x10)
    which = int(path[1],0x10)
    medium = comic.findMedium(com,which)
    checkModified(medium)
    if Session.head: return
    title,description,source = comic.findInfo(com,comicNoExist)
    typ,size,width,height = getStuff(medium)
    with Links:
        if which > 0:
            Links.prev = which - 1
        if comic.pages(com) > which+1:
            Links.next = which + 1
        doScale = User.rescaleImages and size >= maxSize
        link = makeLink(medium,typ,name,
                doScale)

        return makePage(link)
        
def showComic(info,path,params):
    path = path[1:]
    if len(path) == 0:
        return showAllComics(params)
    elif len(path) == 1:
        return showPages(path,params)
    else:
        return showComicPage(path)

class Encoder(json.JSONEncoder):
    def default(self,o):
        note('checking',o)
        try:
            iterable = iter(o)
        except TypeError:
            if hasattr(o,'posi'):
                o = tags.full(o)
                return dict(yea=o.posi,nay=o.nega)
            elif isinstance(o,datetime.datetime):
                return o.isoformat()
        else:
            return tuple(o)
        return super().default(o)

encode = Encoder().encode
