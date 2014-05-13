import dirty.html as d
from dirty import RawString
from place import place
from itertools import count
import fixprint

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
maxSize = 0x20000

def wrappit(s):
    return textwrap.fill(s,width=0x40)

def quote(s):
    try:
        return derp(s).replace('/','%2f')
    except:
        print(repr(s))
        raise

def comment(s):
    return RawString('<!-- '+s+' -->')
def stripPrefix(type):
    if type:
        a = type.split('/',1)
        if len(a)==2:
            return a[1]
        else:
            return 'jpeg'

def degeneralize(tag):
    if tag[:len('general:')]=='general:':
        return tag[len('general:'):]
    return tag

def spaceBetween(elements):
    first = True
    for e in elements:
        if first:
            first = False
        else:
            yield ' '
        yield e

def doTags(top,tags):
    return spaceBetween([d.a(tag,href=top+'/'+quote(tag)+'/') for tag in tags])

def pageLink(id,i=0):
    return place+'/~page/'+'{:x}/'.format(id)

# Cannot set modified from the set of images in this because:
# If the 1st page has a newly added image, the 3rd page will change,
# but the images on the 3rd page will still have older modified times.
# You'd need to request the first page AND the 3rd page, then just use the max modified from
# the first page, for every query. Could just request offset 0 limit 1 I guess...
# withtags.searchTags(tags,negatags,offset=0,limit=1,justModifiedField=True)
# XXX: do this, but write story for now.
# but then you add a tag to the 29th page image, and page 30 changes but page 1 stays the same!

def tail(s,delim):
    i = s.rfind(delim)
    if i == -1:
        return s
    return s[i+1:]

assert tail("test.jpg",".")=='jpg'

def fixType(id):
    import derpmagic as magic
    import filedb
    info = magic.guess_type(filedb.imagePath(id))
    type = info[0]
    if type == 'application/octet-stream':
        raise RuntimeError("Please inspect {:x} could not determine type!".format(id))
    c.execute("UPDATE media SET type = $1 WHERE id = $2",(type,id))
    return type

def fixName(id,type):
    for uri, in c.execute("SELECT uri FROM urisources,media WHERE media.sources @> ARRAY[urisources.id] AND media.id = $1",(id,)):
        name = tail(uri,'/').rstrip('.')
        if name: break
    else:
        name = 'unknown'

    if not '.' in name:
        if type == 'application/octet-stream': 
            type = fixType(id)
        import derpmagic as magic
        name = name + magic.guess_extension(type)

    c.execute("UPDATE media SET name = $1 WHERE id = $2",(name,id))
    return name

def makeLinks(info,linkfor=None):
    if linkfor is None:
        linkfor = pageLink
    counter = count(0)
    row = []
    allexists = True
    for id,name,type,tags in info:
        i = next(counter)
        if i%8==0:
            if row:
                yield d.tr(*row)
            row = []
        tags = [str(tag) for tag in tags]
        if type == 'application/x-shockwave-flash':
            src = '/flash.jpg'
        else:
            fid,oneexists = filedb.check(id)
            allexists = allexists and oneexists
            src='/thumb/'+fid
        link = linkfor(id,i)
        if name is None:
            name = fixName(id,type)
        row.append(d.td(d.a(d.img(src=src,alt="...",title=' '+name+' '),href=link),d.br(),d.sup('...',title=wrappit(', '.join(tags))) if tags else '',href=link))
    if row: yield d.tr(*row)
    Session.refresh = not allexists

def makeBase():
    # drop bass
    return 'http://[fcd9:e703:498e:5d07:e5fc:d525:80a6:a51c]/art/'

@context.Context
class Links:
    next = None
    prev = None
    style = "/style/art.css"
    id = None

def standardHead(title,*contents):
    # oembed sucks:
    if Links.id:
        url = urljoin(makeBase(),'/art/~page/{:x}/'.format(Links.id))
    return d.head(d.title(title),
            d.meta(charset='utf-8'),
        d.link(rel="icon",type="image/png",href="/favicon.png"),
        d.link(rel='stylesheet',type='text/css',href=Links.style),
        d.link(rel='next',href=Links.next if Links.next else ''),
        d.link(rel='prev',href=Links.prev if Links.prev else ''),
        d.link(rel='alternate',type='application/json+oembed',href='/art/~oembed/{:x}?url={}'.format(Links.id,
            # oembed sucks:
            quote(url))) if Links.id else '',
        *contents)

def makePage(title,*content):
    content = content + (
        d.p(d.a("User Settings",href=("/art/~user"))),)
    return d.xhtml(standardHead(title),d.body(
#        d.p(d.a(d.img(src="/stuff/derp.gif"),href="/stuff/derp.html")),
        *content))

def makeE(tag):
    tag = d.Tag(tag)
    def makeE(*a,**kw):
        return d.Element(tag,*a,**kw)
    return makeE
audio = makeE('audio')
video = makeE('video')
source = makeE('source')
embed = makeE('embed')

def makeLink(type,thing,width=None):
    if type.startswith('text'):
        return d.pre(thing)
    if type.startswith('image'):
        attrs = {'src': thing,
                'alt': 'Still resizing...'}
        if width: 
            attrs['width'] = width
        return d.img(attrs)
    wrapper = None
    if type.startswith('audio') or type.startswith('video') or type == 'application/octet-stream':
        if False:#type.endswith('webm') or type.endswith('ogg'):
            if type[0]=='a':
                wrapper = audio
            else:
                wrapper = video
            return wrapper(source(src=thing,type=type),
                    d.object(
                        embed(src=thing,width='100%',height='100%',type=type),
                        data=thing,height='100%',width='100%',type=type),
                        autoplay=True,loop=True)
        else:
            return d.object(d.param(name='src',value=thing),height='100%',width='100%',type=type,loop=True,autoplay=True),embed(' ',src=thing,width='100%',height='100%',type=type,loop=True,autoplay=True),"Download"
    if type == 'application/x-shockwave-flash':
        return d.object(d.param(name='SRC',value=thing),
                embed(' ',src=thing,width="100%", height="100%"),
                width='100%',height='100%'),'Download'
    raise RuntimeError("What is "+type)

def imageLink(id,type):
    return '/image/{:x}/{}'.format(id,type)

def simple(info,path,params):
    if Session.head: return
    id,type = info
    return makePage("derp",d.a(d.img(src=imageLink(id,type)),href=pageLink(id)))

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
        id,next,prev,name,type,width,size,modified,tags = info
    
    doScale = not 'ns' in params
    doScale = doScale and User.rescaleImages and size > maxSize

    if Session.head:
        if doScale: 
            fid, exists = filedb.checkResized(id)
            Session.refresh = not exists
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
    if doScale:
        fid,exists = filedb.checkResized(id)
        thing = '/resized/'+fid+'/donotsave.this'
        Session.refresh = not exists
    else:
        fid = '{:x}'.format(id)
        thing = '/'.join(('/image',fid,type,name))
    if tags:
        tagderp = d.p("Tags: ",((' ',d.a(tag[0],id=tag[1],class_='tag',href=place+"/"+quote(tag[0]))) for tag in tags))
    else:
        tagderp = ''
    # even if not rescaling, sets img width unless ns in params
    thing = makeLink(type,thing,width if doScale else None)
    with Links:
        if next:
            Links.next = '../{:x}/'.format(next)+unparseQuery()
        if prev:
            Links.prev = '../{:x}/'.format(prev)+unparseQuery()
        return makePage("Page info for "+fid,
                comment("Tags: "+boorutags),
                d.p(d.a(thing,id='image',href='/'.join(('/image',fid,type,name)))),
                d.p(d.a('Info',href=place+"/~info/"+fid)),
                tagderp)

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
    sources = [(id,derp.source(id)) for id in info['sources']]
    sources = [pair for pair in sources if pair[1]]
    keys = sorted(info.keys())
    fid,exists = filedb.check(id)
    Session.refresh = not exists
    return makePage("Info about "+fid,
            d.p(d.a(d.img(src=thumbLink(id)),d.br(),"Page",href=pageLink(id))),
            d.table((d.tr(d.td(key),d.td(stringize(info[key]))) for key in keys if key != "sources" and key != "id"),Class='info'),
            d.hr(),
            "Sources",
            (d.p(d.a(source,href=source)) for id,source in sources))

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
    if not tags or negatags: return place+'/'
    return place+'/'+"/".join([quote(tag) for tag in tags]+['-'+quote(tag) for tag in negatags])+'/'

def stripGeneral(tags):
    return [tag.replace('general:','') for tag in tags]

def images(url,query,offset,info,related,basic):
    #related = tags.names(related) should already be done
    basic = tags.names(basic)
    related=stripGeneral(related)

    removers = []
    for tag in basic.posi:
        removers.append(d.a(tag,href=tagsURL(basic.posi.difference(set([tag])),defaultTags.nega)))
    for tag in basic.nega:
        removers.append(d.a(tag,href=tagsURL(basic.posi,basic.nega.difference(set([tag])))))

    with Links:
        info = list(info)
        if len(info)>=0x30:
            print('offset + 1 {:x} {:x}',offset,offset+1)
            query['o'] = offset + 1
            Links.next = url.path+unparseQuery(query)
        if offset > 0:
            query['o'] = offset - 1
            Links.prev = url.path+unparseQuery(query)
        return makePage("Images",
                d.p("You are ",d.a(User.ident,href="/art/~user")),
                d.table(makeLinks(info)),
                (d.p("Related tags",d.hr(),doTags(url.path.rstrip('/'),related)) if related else ''),
                (d.p("Remove tags",d.hr(),spaceBetween(removers)) if removers else ''),
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
            d.p(d.a(d.img(src="/".join(("","image",'{:x}'.format(current),type,name))),
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
        result = ((row[0],row[1]=='t') for row in result)
    tagnames = []
    for name,nega in result:
        if nega:
            name = '-'+name
        tagnames.append(name)
    tagnames = ', '.join(tagnames)

    return makePage("User Settings",
        d.form(
        d.ul(
            d.li("Rescale Images? ",rescalebox),
            d.li("Implied Tags",d.input(type='text',name='tags',value=tagnames)),
            d.li(d.input(type="submit",value="Submit"))),
        method="post",
        enctype="multipart/form-data"))

def getPage(params):
    page = params.get('p')
    if not page:
        return 0
    else:
        return int(page[0])

def getType(image):
    return c.execute("SELECT type FROM media WHERE id = $1",(image,))[0][0]

def comicPageLink(com,isDown=False):
    def pageLink(image=None,counter=None):
        if isDown:
            link = ''
        else:
            link = '../'
        link = link + '{:x}/'.format(com)
        return link + unparseQuery()
    return pageLink

def comicNoExist():
    raise RuntimeError("Comic no exist")

def checkModified(image):
    modified = c.execute('SELECT EXTRACT(EPOCH FROM modified) FROM media WHERE id = $1',(image,))[0][0]
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
                image = comic.findImage(id,0)
            except Redirect: 
                image = 0x5c911
            if not image: 
                image = 0x5c911
            checkModified(image)
            yield image,title,getType(image),()
    if Session.head:
        for stuff in getInfos(): pass
        return
    with Links:
        if page > 0:
            Links.prev = unparseQuery({'p':page-1})
        if page + 1 < comic.numComics() / 0x20:
            Links.next = unparseQuery({'p':page+1})
        def formatLink(image,i):
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
    def getImages():
        for which in range(offset,min(0x20+offset,numPages)):
            image = comic.findImage(com,which)
            checkModified(image)
            yield image,which
    if Session.head:
        for stuff in getImages(): pass
        return
    title,description,source = comic.findInfo(com,comicNoExist)
    if not description: description = 'ehunno' 
    def getInfos():
        for image,which in getImages():
            yield image,title + ' page {}'.format(which),getType(image),()
    with Links:
        if page > 0:
            Links.prev = unparseQuery({'p':page-1})
        if page + 1 < numPages:
            Links.next = unparseQuery({'p':page+1})
        return makePage(title + " - Comics",
                d.h1(title),
                d.table(makeLinks(getInfos(),lambda image,i: '{:x}/'.format(i+offset))) if numPages else '',
                d.p(RawString(description)),
                d.p(d.a('Source',href=source)) if source else '',
                d.p((d.a("Prev ",href=Links.prev) if Links.prev else ''),
                    d.a("Index",href=".."),
                    (d.a(" Next",href=Links.next)if Links.next else '')))

def showComicPage(path):
    com = int(path[0],0x10)
    which = int(path[1],0x10)
    image = comic.findImage(com,which)
    checkModified(image)
    if Session.head: return
    title,description,source = comic.findInfo(com,comicNoExist)
    typ = getType(image)
    name = title + '.' + typ.rsplit('/',1)[-1]
    with Links:
        if which > 0:
            Links.prev = comicPageLink(which-1)()
        if comic.pages(com) > which+1:
            Links.next = comicPageLink(which+1)()
        else:
            Links.next = ".."
        image = comic.findImage(com,which)
        return makePage("{:x} page ".format(which)+title,
                d.p(d.a(d.img(src='/image/{:x}/{}/{}'.format(image,typ,name),width='100%'),href=Links.next)),
                d.p((d.a("Prev ",href=Links.prev) if Links.prev else ''),                    
                    d.a("Index",href=".."),
                    (d.a(" Next",href=Links.next)if Links.next else '')),
                d.p(d.a("Page",href="/art/~page/{:x}".format(image))))
        
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
