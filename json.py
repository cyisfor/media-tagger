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

def standardHead(title,*contents):
    ret = {'title': title}
    if Links.prev:
        ret['prev'] = Links.prev
    if Links.next:
        ret['next'] = Links.next
    if Links.id:
        ret['id'] = Links.id

def makePage(title,**kw):
    ret = standardHead(title)
    ret['content'] = kw

def makeLink(id,type,name,width=None,height=None,style=None):
    fid,exists = filedb.checkResized(id,create=False)
        resized = '/resized/'+fid+'/donotsave.this'
        Session.refresh = not exists and isImage
    else:
        fid = '{:x}'.format(id)
        resized = None

    if not style:
        if isImage is None:
            isImage = type.startswith('image')
        if not isImage:
            if width:
                style="width: "+str(width)+'px;'
            else:
                style = None
            if height:
                sty = ' height: '+str(height)+'px;'
                style = style + sty if style else sty

    thing = '/'.join(('/media',fid,type,name))

    if type.startswith('text'):
        return fid,d.pre(thing),thing
    if type.startswith('image'):
        if doScale:
            height = width = None # already resized the pixels
        if resized:
            return fid,d.img(src=resized,alt='Still resizing...'),thing
        else:
            return fid,d.img(src=thing,style=style),thing
    # can't scale videos, so just adjust their width/height in CSS
    wrapper = None
    if type.startswith('audio') or type.startswith('video') or type == 'application/octet-stream':
        if type.endswith('webm') or type.endswith('ogg'):
            if type[0]=='a':
                wrapper = audio
            else:
                wrapper = video
            return fid,wrapper(source(src=thing,type=type),
                    d.object(
                        embed(src=thing,style=style,type=type),
                        width=width, height=height,
                        data=thing,style=style,type=type),
                        autoplay=True,loop=True),thing
        else:
            return fid,(d.object(
                    embed(' ',src=thing,style=style,type=type,loop=True,autoplay=True),
                    d.param(name='src',value=thing),
                        style=style,
                        type=type,
                        loop=True,
                        autoplay=True, 
                        width=width, 
                        height=height),d.br(),"Download"),thing
    if type == 'application/x-shockwave-flash':
        return fid,(d.object(d.param(name='SRC',value=thing),
                embed(' ',src=thing,style=style),
                style=style),d.br(),'Download'),thing
    raise RuntimeError("What is "+type)

def mediaLink(id,type):
    return '/media/{:x}/{}'.format(id,type)

def simple(info,path,params):
    if Session.head: return
    id,type = info
    return makePage("derp",d.a(d.img(src=mediaLink(id,type)),href=pageLink(id)))

def resized(info,path,params):
    id = int(path[1],0x10)
    while True:
        fid, exists = filedb.checkResized(id)
        if exists: break
    raise Redirect("/resized/"+fid+"/donotsave.this")

def page(info,path,params):
    if Session.head:
        id,modified,size = info
    else:
        id,next,prev,name,type,width,height,size,modified,tags,comic = info

    doScale = not 'ns' in params
    doScale = doScale and User.rescaleImages and size >= maxSize

    if Session.head:
        if doScale: 
            fid, exists = filedb.checkResized(id)
            Session.refresh = not exists and type.startswith('image')
        Session.modified = modified
        return
    Links.id = id
    Session.modified = modified
    if name:
        name = quote(name)
        if not '.' in name:
            name = name + '/untitled.jpg'
    else:
        name = 'untitled.jpg'
    tags = [str(tag) if not isinstance(tag,str) else tag for tag in tags]
    tags = [(degeneralize(tag),tag) for tag in tags]
    boorutags = " ".join(tag[0].replace(' ','_') for tag in tags)
    # even if not rescaling, sets img width unless ns in params
    fid,link,thing = makeLink(id,type,name,doScale,width,height)
    tail = []
    def pageURL(id):
        return '../{:x}'.format(id)
    def updateComic(comic):
        def comicURL(id):
            return '/art/~comic/{:x}/'.format(id)
        comic, title, prev, next = comic
        tail.append(d.p("Comic: ",d.a(title,href=comicURL(comic)),' ',d.a('<<',href=pageURL(prev)) if prev else None,d.a('>>',href=pageURL(next)) if next else None))
    if comic:
        updateComic(comic)
    if tags:
        tail.append(d.p("Tags: ",((' ',d.a(tag[0],id=tag[1],class_='tag',href=place+"/"+quote(tag[0]))) for tag in tags)))
    with Links:
        if next:
            Links.next = pageURL(next)+unparseQuery()
        if prev:
            Links.prev = pageURL(prev)+unparseQuery()
        return makePage("Page info for "+fid,
                comment("Tags: "+boorutags),
                d.p(d.a(link,id='mediumu',href=thing)),
                d.p(d.a('Info',href=place+"/~info/"+fid)),
                tail)

def stringize(key):
    if hasattr(key,'isoformat'):
        return key.isoformat()
    elif isinstance(key,str):
        return key
    elif isinstance(key,bytes):
        return key.decode('utf-8')
    return str(key)

def thumbLink(id):
    return "/thumb/"+'{:x}'.format(id)

def info(info,path,params):
    Session.modified = info['sessmodified']
    if Session.head: return
    del info['sessmodified']
    import info as derp
    id = info['id']
    sources = info['sources']
    if sources is None:
        sources = ()
    else:
        sources = ((id,derp.source(id)) for id in sources)
        sources = [pair for pair in sources if pair[1]]
    keys = set(info.keys())
    keys.discard('id')
    keys.discard('sources')
    keys = sorted(keys)
    fid,exists = filedb.check(id)
    Session.refresh = not exists
    tags = [str(tag) if not isinstance(tag,str) else tag for tag in info['tags']]
    info['tags'] = ', '.join(tags)

    return makePage("Info about "+fid,
            d.p(d.a(d.img(src=thumbLink(id)),d.br(),"Page",href=pageLink(id))),
            d.table((d.tr(d.td(key),d.td(stringize(info[key]),id=key)) for key in keys),Class='info'),
            d.hr(),
            "Sources",
            d.span((d.p(d.a(source,href=source)) for id,source in sources),id='sources'))

def like(info):
    return "Under construction!"

def unparseQuery(query={}):
    for n,v in Session.params.items():
        query.setdefault(n,v)
    result = []
    for n,v in query.items():
        if isinstance(v,list) or isinstance(v,tuple) or isinstance(v,set):
            for vv in v:
                result.append((n,vv))
        elif isinstance(v,int):
            result.append((n,'{:x}'.format(v)))
        else:
            result.append((n,v))
    if result:
        return '?'+'&'.join(n+'='+v for n,v in result)
    return ''

def tagsURL(tags,negatags):
    if not (tags or negatags): return place+'/'
    res = place+'/'+"/".join([quote(tag) for tag in tags]+['-'+quote(tag) for tag in negatags])+'/'
    return res

def stripGeneral(tags):
    return [tag.replace('general:','') for tag in tags]

def media(url,query,offset,info,related,basic):
    #related = tags.names(related) should already be done
    basic = tags.names(basic)
    related=stripGeneral(related)

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
