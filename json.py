import process
from note import note
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
        for id,name,type,tags in info:
            i = next(counter)
            tags = [str(tag) for tag in tags]
            fid,oneexists = filedb.check(id,create=False)
            allexists = allexists and oneexists
            yield dict(id=id,exists=onexists,name=name,type=type,tags=tags)
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
    if Links.prev:
        ret['prev'] = Links.prev
    if Links.next:
        ret['next'] = Links.next
    if Links.id:
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
        fid,exists = filedb.check(id,'media',create=False)

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

    doScale = doScale and User.rescaleImages and size >= maxSize

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
    related = tags.nomenclature(related)
    basic = tags.nomenclature(basic)

    removers = []
    for tag in basic.posi:
        removers.append(d.a(tag,href=tagsURL(basic.posi.difference(set([tag])),basic.nega)))
    for tag in basic.nega:
        removers.append(d.a('-'+tag,href=tagsURL(basic.posi,basic.nega.difference(set([tag])))))

    with Links:
        info = list(info)
        if len(info)>=thumbnailPageSize:
            query['o'] = offset + 1
            Links.next = url.path+unparseQuery(query)
        if offset > 0:
            query['o'] = offset - 1
            Links.prev = url.path+unparseQuery(query)
        return makePage("Media "+str(basic),
                d.p("You are ",d.a(User.ident,href=place+"/~user")),
                d.table(makeLinks(info)),
                (d.div("Related tags",d.hr(),doTags(url.path.rstrip('/'),related),id='related') if related else ''),
                (d.div("Remove tags",d.hr(),spaceBetween(removers),id='remove') if removers else ''),
                d.p((d.a('Prev',href=Links.prev),' ') if Links.prev else '',(d.a('Next',href=Links.next) if Links.next else '')))

def desktop(raw,path,params):
    import desktop
    if 'n' in params:
        n = int(params['n'][0],0x10)
    else:
        n = 0x10
    history = desktop.history(n)
    if not history:
        return "No desktops yet!?"
    if 'd' in params:
        raise Redirect(pageLink(0,history[0]))
    if Session.head:
        Session.modified = c.execute("SELECT EXTRACT(EPOCH FROM modified) FROM media WHERE media.id = $1",(history[0],))[0][0]
        return
    if n == 0x10:
        current = history[0]
        history = history[1:]
        name,type,tags = c.execute("SELECT name,type,array(select name from tags where tags.id = ANY(neighbors)) FROM media INNER JOIN things ON things.id = media.id WHERE media.id = $1",(current,))[0]
        tags = [str(tag) for tag in tags]
        type = stripPrefix(type)
        middle = (
            d.p("Having tags ",doTags(place,tags)),
            d.p(d.a(d.img(src="/".join(("","media",'{:x}'.format(current),type,name))),
                href=pageLink(current,0))),
            d.hr())
    else:
        middle = ''
    def makeDesktopLinks():
        allexists = True
        for id,name in c.execute("SELECT id,name FROM media WHERE id = ANY ($1::bigint[])",(history,)):
            fid,exists = filedb.check(id) 
            allexists = allexists and exists
            yield d.td(d.a(d.img(title=name,src="/thumb/"+fid,alt=name),
                            href=pageLink(id)))
        Session.refresh = not allexists
    def makeDesktopRows():
        row = []
        for td in makeDesktopLinks():
            row.append(td)
            if len(row) == 8:
                yield d.tr(row)
                row = []
        if len(row):
            yield d.tr(row)

    Session.modified = c.execute("SELECT EXTRACT (epoch from MAX(added)) FROM media")[0][0]
    return makePage("Current Desktop",
            middle,
            d.p("Past Desktops"),
            d.div(
                d.table(
                    makeDesktopRows())))

def user(info,path,params):
    if Session.head: return
    if 'submit' in params:
        process.user(path,params)
        raise Redirect(place+'/~user')
    iattr = {
            'type': 'checkbox',
            'name': 'rescale'}
    if User.rescaleImages:
        iattr['checked'] = True
    rescalebox = d.input(iattr)
    if User.defaultTags:
        def makeResult():
            result = c.execute("SELECT tags.name FROM tags WHERE id = ANY($1::bigint[])",(defaultTags.posi,))
            for name in result:
                yield name[0],False
            result = c.execute("SELECT tags.name FROM tags WHERE id = ANY($1::bigint[])",(defaultTags.nega,))
            for name in result:
                yield name[0],True
        result = makeResult()
    else:
        result = c.execute('SELECT tags.name,uzertags.nega FROM tags INNER JOIN uzertags ON tags.id = uzertags.tag WHERE uzertags.uzer = $1',(User.id,))
        note('raw uzer tag result',result)
        result = ((row[0],row[1] is True or row[1]=='t') for row in result)
    tagnames = []
    for name,nega in result:
        if nega:
            name = '-'+name
        tagnames.append(name)
    tagnames = ', '.join(tagnames)
    note('tagnames',tagnames)
    return makePage("User Settings",
        d.form(
        d.ul(
            d.li("Rescale Media? ",rescalebox),
            d.li("Implied Tags",d.input(type='text',name='tags',value=tagnames)),
            d.li(d.input(type="submit",value="Submit"))),
        action=place+'/~user/',
        type='application/x-www-form-urlencoded',
        method="post"),
        d.p(d.a('Main Page',href=place)),
        nouser=True)

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
            yield medium,title,getType(medium),()
    if Session.head:
        for stuff in getInfos(): pass
        return
    with Links:
        if page > 0:
            Links.prev = unparseQuery({'p':page-1})
        if page + 1 < comic.numComics() / 0x20:
            Links.next = unparseQuery({'p':page+1})
        def formatLink(medium,i):
            if comic.pages(comics[i][0]) == 0:
                return '{:x}/'.format(comics[i][0])
            return '{:x}/0/'.format(comics[i][0])
        links = makeLinks(getInfos(),formatLink)
        return makePage("{:x} Page Comics".format(page),
                d.table(links),
                d.p((d.a("Prev",href=Links.prev) if Links.prev else ''),
                    (' ' if Links.prev and Links.next else ''),
                    (d.a("Next",href=Links.next)if Links.next else '')))
def showPages(path,params):
    com = int(path[0],0x10)
    page = getPage(params)
    offset = page * 0x20
    if offset and offset >= comic.pages(com):
        raise Redirect('..')
    numPages = comic.pages(com)
    def getMedia():
        for which in range(offset,min(0x20+offset,numPages)):
            medium = comic.findMedium(com,which)
            checkModified(medium)
            yield medium,which
    if Session.head:
        for stuff in getMedia(): pass
        return
    title,description,source = comic.findInfo(com,comicNoExist)
    if not description: description = 'ehunno' 
    def getInfos():
        for medium,which in getMedia():
            yield medium,title + ' page {}'.format(which),getType(medium),()
    with Links:
        if page > 0:
            Links.prev = unparseQuery({'p':page-1})
        if page + 1 < numPages:
            Links.next = unparseQuery({'p':page+1})
        return makePage(title + " - Comics",
                d.h1(title),
                d.table(makeLinks(getInfos(),lambda medium,i: '{:x}/'.format(i+offset))) if numPages else '',
                d.p(RawString(description)),
                d.p(d.a('Source',href=source)) if source else '',
                d.p((d.a("Prev ",href=Links.prev) if Links.prev else ''),
                    d.a("Index",href=".."),
                    (d.a(" Next",href=Links.next)if Links.next else '')))

def showComicPage(path):
    com = int(path[0],0x10)
    which = int(path[1],0x10)
    medium = comic.findMedium(com,which)
    checkModified(medium)
    if Session.head: return
    title,description,source = comic.findInfo(com,comicNoExist)
    typ,size,width,height = getStuff(medium)
    name = title + '.' + typ.rsplit('/',1)[-1]
    with Links:
        if which > 0:
            Links.prev = comicPageLink(which-1)()
        if comic.pages(com) > which+1:
            Links.next = comicPageLink(which+1)()
        else:
            Links.next = ".."
        medium = comic.findMedium(com,which)
        doScale = User.rescaleImages and size >= maxSize
        fid,link,thing = makeLink(medium,typ,name,
                doScale,style='width: 100%')

        return makePage("{:x} page ".format(which)+title,
                d.p(d.a(link,href=Links.next)),
                d.p((d.a("Prev ",href=Links.prev) if Links.prev else ''),                    
                    d.a("Index",href=".."),
                    (d.a(" Next",href=Links.next)if Links.next else '')),
                d.p(d.a("Page",href="/art/~page/"+fid),(' ',d.a("Medium",href=thing)) if doScale else None))
        
def showComic(info,path,params):
    path = path[1:]
    if len(path) == 0:
        return showAllComics(params)
    elif len(path) == 1:
        return showPages(path,params)
    else:
        return showComicPage(path)
        
def oembed(info, path, params):
    Session.type = 'application/json'
    if Session.head: return
    id,tags = info
    base = makeBase()
    xid, exists = filedb.check(id)
    thumb = urljoin(base,thumbLink(id))
    response = {
            'type': 'photo',
            'tags': tags,
            'version': 1.0,
            'url': thumb,
            'width': 150,
            'height': 150,
            'thumbnail_url': thumb,
            'thumbnail_width': 150,
            'thumbnail_height': 150,
            'provider_url': base,
            }
    return json.dumps(response)
