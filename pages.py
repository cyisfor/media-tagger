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

from urllib.parse import quote as derp
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
    return place+'/~page/'+'{:x}'.format(id)

# Cannot set modified from the set of images in this because:
# If the 1st page has a newly added image, the 3rd page will change,
# but the images on the 3rd page will still have older modified times.
# You'd need to request the first page AND the 3rd page, then just use the max modified from
# the first page, for every query. Could just request offset 0 limit 1 I guess...
# withtags.searchTags(tags,negatags,offset=0,limit=1,justModifiedField=True)
# XXX: do this, but write story for now.
# but then you add a tag to the 29th page image, and page 30 changes but page 1 stays the same!

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
        type = stripPrefix(type)
        link = linkfor(id,i)
        row.append(d.td(d.a(d.img(src=src,alt="...",title=' '+name+' '),href=link),d.br(),d.sup('...',title=wrappit(', '.join(tags))) if tags else '',href=link))
    if row: yield d.tr(*row)
    Session.refresh = not allexists

@context.Context
class Links:
    next = None
    prev = None
    style = "/style/art.css"

def standardHead(title,*contents):
    if Session.params:
        params = []
        for name,values in Session.params.items():
            for value in values:
                params.append(name+'='+quote(value))
        params = '?' + '&'.join(params)
    else:
        params = ''
    return d.head(d.title(title),
            d.meta(charset='utf-8'),
        d.link(rel='stylesheet',type='text/css',href=Links.style),
        d.link(rel='next',href=Links.next+params) if Links.next else '',
        d.link(rel='prev',href=Links.prev+params) if Links.prev else '',
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

def simple(info,path,params):
    id,type = info
    return makePage("derp",d.a(d.img(src='/image/{:x}/{}'.format(id,type)),href=pageLink(id)))

def page(info,path,params):
    id,next,prev,name,type,width,size,modified,tags = info
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
    doScale = not 'ns' in params
    if doScale and User.rescaleImages and size > maxSize:
        fid,exists = filedb.checkResized(id)
        thing = '/resized/'+fid+'/donotsave.this'
        Session.refresh = not exists
        type = 'image/jpeg'
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
            Links.next = '../{:x}/'.format(next)
        if prev:
            Links.prev = '../{:x}/'.format(prev)
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

def info(info,path,params):
    Session.modified = info['sessmodified']
    del info['sessmodified']
    import info as derp
    id = info['id']
    sources = [(id,derp.source(id)) for id in info['sources']]
    sources = [pair for pair in sources if pair[1]]
    keys = sorted(info.keys())
    return makePage("Info about "+'{:x}'.format(id),
            d.p(d.a(d.img(src="/thumb/"+'{:x}'.format(id)),d.br(),"Page",href=pageLink(id))),
            d.table((d.tr(d.td(key),d.td(stringize(info[key]))) for key in keys if key != "sources" and key != "id"),Class='info'),
            d.hr(),
            "Sources",
            (d.p(d.a(str(id)+': '+source,href=source)) for id,source in sources))

def like(info):
    return "Under construction!"

def unparseQuery(query):
    return '&'.join(tuple('&'.join((n+'='+vv) for vv in v) for n,v in query.items()))

def tagsURL(tags,negatags):
    if not tags or negatags: return place+'/'
    return place+'/'+"/".join([quote(tag) for tag in tags]+['-'+quote(tag) for tag in negatags])+'/'

def stripGeneral(tags):
    return [tag.replace('general:','') for tag in tags]

def images(url,query,offset,info,related,basic):
    #related = tags.names(related) should already be done
    basic = tags.names(basic)
    related=stripGeneral(related)
    query['o'] = ['{:x}'.format(offset+1)]

    removers = []
    for tag in basic.posi:
        removers.append(d.a(tag,href=tagsURL(basic.posi.difference(set([tag])),defaultTags.nega)))
    for tag in basic.nega:
        removers.append(d.a(tag,href=tagsURL(basic.posi,basic.nega.difference(set([tag])))))

    with Links:
        info = list(info)
        if len(info)>=0x30:
            Links.next = url.path+'?'+unparseQuery(query)
        if offset != 0:
            query['o'] = ['{:x}'.format(offset-1)]
            Links.prev = url.path+('?'+unparseQuery(query) if offset > 1 else '')
        return makePage("Images",
                d.p("You are ",d.a(User.ident,href="/art/~user")),
                d.table(makeLinks(info)),
                (d.p("Related tags",d.hr(),doTags(url.path.rstrip('/'),related)) if related else ''),
                (d.p("Remove tags",d.hr(),spaceBetween(removers)) if removers else ''),
                d.p((d.a('Prev',href=Links.prev),' ') if Links.prev else '',(d.a('Next',href=Links.next) if Links.next else '')))

def desktop(raw,path,params):
    import desktop
    history = desktop.history()
    if not history:
        return "No desktops yet!?"
    if 'd' in params:
        raise Redirect(pageLink(0,history[0]))
    current = history[0]
    history = history[1:]
    name,type,tags = c.execute("SELECT name,type,array(select name from tags where tags.id = ANY(neighbors)) FROM media INNER JOIN things ON things.id = media.id WHERE media.id = $1",(current,))[0]
    tags = [str(tag) for tag in tags]
    type = stripPrefix(type)
    def makeDesktopLinks():
        allexists = True
        for id,name in c.execute("SELECT id,name FROM media WHERE id = ANY ($1::bigint[])",(history,)):
            fid,exists = filedb.check(id) 
            allexists = allexists and exists
            return d.td(d.a(d.img(title=name,src="/thumb/"+fid,alt=name),
                            href=pageLink(id)))
        Session.refresh = not allexists

    Session.modified = db.c.execute("SELECT EXTRACT (epoch from MAX(added)) FROM media")[0][0]
    return makePage("Current Desktop",
            d.p("Having tags ",doTags(place,tags)),
            d.p(d.a(d.img(src="/".join(("","image",'{:x}'.format(current),type,name))),
                href=pageLink(0,current))),
            d.hr(),
            d.p("Past Desktops"),
            d.div(
                d.table(
                    d.tr(makeDesktopLinks()))))

def user(info,path,params):
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
        result = c.execute('SELECT tags.name,uzertags.nega FROM tags INNER JOIN uzertags ON tags.id = uzertags.id WHERE uzertags.uzer = $1',(User.id,))
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
        return link
    return pageLink

def comicNoExist():
    raise RuntimeError("Comic no exist")

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
            yield image,title,getType(image),()
    with Links:
        if page > 0:
            Links.prev = "?p={}".format(page-1)
        if page + 1 < comic.numComics() / 0x20:
            Links.next = "?p={}".format(page+1)
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
    title,description,source = comic.findInfo(com,comicNoExist)
    if not description: description = 'ehunno' 
    numPages = comic.pages(com)
    def getInfos():
        for which in range(offset,min(0x20+offset,numPages)):
            image = comic.findImage(com,which)
            yield image,title + ' page {}'.format(which),getType(image),()
    with Links:
        if page > 0:
            Links.prev = "?p={}".format(page-1)
        if page + 1 < numPages:
            Links.next = "?p={}".format(page+1)
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
        
