
import fixprint

from dimensions import thumbnailPageSize,thumbnailRowSize

import comic
from user import User,dtags as defaultTags
from session import Session
import tags
import context
import db
from redirect import Redirect
import filedb

import process
from note import note
import explanations

from schlorp import schlorp

import dirty.html as d
from dirty import RawString
from place import place
from itertools import count

from tornado import gen
from tornado.gen import Return

try:
    from numpy import mean
except ImportError:
    def mean(l):
        i = 0
        s = 0
        for n in l:
            i += 1
            s += n
        return s / i

import re
import json
from urllib.parse import quote as derp, urljoin
import time
import os

import textwrap

maxWidth = 800
maxSize = 0x40000

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

def tuplize(f):
    def wrapper(*a,**kw):
        return tuple(f(*a,**kw))
    return wrapper

@tuplize
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

# Cannot set modified from the set of media in this because:
# If the 1st page has a newly added medium, the 3rd page will change,
# but the media on the 3rd page will still have older modified times.
# You'd need to request the first page AND the 3rd page, then just use the max modified from
# the first page, for every query. Could just request offset 0 limit 1 I guess...
# withtags.searchTags(tags,negatags,offset=0,limit=1,justModifiedField=True)
# XXX: do this, but write story for now.
# but then you add a tag to the 29th page medium, and page 30 changes but page 1 stays the same!

def tail(s,delim):
    i = s.rfind(delim)
    if i == -1:
        return s
    return s[i+1:]

assert tail("test.jpg",".")=='jpg'

def fixType(id):
    import derpmagic as magic
    import filedb
    info = magic.guess_type(filedb.mediumPath(id))
    type = info[0]
    if type == 'application/octet-stream':
        raise RuntimeError("Please inspect {:x} could not determine type!".format(id))
    db.execute("UPDATE media SET type = $1 WHERE id = $2",(type,id))
    return type

def fixName(id,type):
    for uri, in db.execute("SELECT uri FROM urisources INNER JOIN media ON media.sources @> ARRAY[urisources.id] AND media.id = $1",(id,)):
        name = tail(uri,'/').rstrip('.')
        if name: break
    else:
        name = 'unknown'

    if not '.' in name:
        if type == 'application/octet-stream':
            type = fixType(id)
        import derpmagic as magic
        name = name + magic.guess_extension(type)

    db.execute("UPDATE media SET name = $1 WHERE id = $2",(name,id))
    return name

@gen.coroutine
def makeLinks(info,linkfor=None):
    if linkfor is None:
        linkfor = pageLink
    counter = count(0)
    row = []
    rows = []
    allexists = True
    for id,name,type,tags in info:
        i = next(counter)
        if i%thumbnailRowSize==0:
            if row:
                #rows.append(row)
                rows.append((tuple(row)+(d.br(),)))
            row = []
        tags = [str(tag) for tag in tags]
        if type == 'application/x-shockwave-flash':
            src = '/flash.jpg'
        else:
            fid,oneexists = yield filedb.check(id)
            allexists = allexists and oneexists
            src='/thumb/'+fid
        link = linkfor(id,i)
        if name is None:
            name = fixName(id,type)
        #row.append(d.td(d.a(d.img(src=src,alt="h",title=' '+name+' '),href=link),d.br(),d.sup('(i)',title=wrappit(', '.join(tags))) if tags else '',href=link))
        taginfo = d.span('(i)',title=wrappit(', '.join(tags)
                                           if tags else ''),
                         href=link,
                         class_='taghi')
        link = d.a(d.img(src=src,title=' '+name+' '),href=link)
        row.append(d.div(link,taginfo,class_='thumb'))
                    
    if row: rows.append((tuple(row)+(d.br(),)))
    Session.refresh = not allexists
    raise Return(rows)

def makeBase():
    # drop bass
    return 'http://[fcd9:e703:498e:5d07:e5fc:d525:80a6:a51c]/art/'

@context.Context
class Links:
    next = None
    prev = None
    id = None

# meh
# style = schlorp(os.path.join(filedb.base,"style.css"),text=False)

def standardHead(title,*contents):
    # oembed sucks:
    if Links.id:
        url = urljoin(makeBase(),'/art/~page/{:x}/'.format(Links.id))
    return d.head(
        d.title(title),
        d.meta(charset='utf-8'),
        d.meta(name="og:title",value=title),
        d.meta(name="og:type",value="website"),
        d.meta(name="og:image",value=("/thumb/{:x}".format(Links.id) if Links.id else "/thumb/5d359")),
        d.meta(name="og:url",value=url if Links.id else makeBase()),
        d.link(rel="icon",type="image/png",href="/favicon.png"),
        d.link(rel='stylesheet',type='text/css',href="/style/art.css"),
        d.link(rel='next',href=Links.next if Links.next else ''),
        d.link(rel='prev',href=Links.prev if Links.prev else ''),
        d.link(rel='alternate',type='application/json+oembed',href='/art/~oembed/{:x}?url={}'.format(Links.id,
            # oembed sucks:
            quote(url))) if Links.id else '',
        *contents)

def makePage(title,*content,**kw):
    if kw.get('nouser') is None:
        content = content + (
            d.p(d.a("User Settings",href=("/art/~user"))),)
    return d.xhtml(standardHead(title),d.body(
#		d.p(d.a(d.img(src="/stuff/derp.gif"),href="/stuff/derp.html")),
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

def makeStyle(s):
    res = ''
    for selector,props in s:
        res += selector + '{\n';
        for n,v in props.items():
            res += '\t'+n+': '+v+';\n'
        res += '}\n'
    return d.style(res,type='text/css')

@gen.coroutine
def makeLink(id,type,name,doScale,width=None,height=None,style=None):
    isImage = None
    if doScale:
        isImage = type.startswith('image')
        fid,exists = yield filedb.checkResized(id)
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
        raise Return((fid,d.pre(thing),thing))
    if type.startswith('image'):
        if doScale:
            height = width = None # already resized the pixels
        if resized:
            raise Return((fid,d.img(class_='wid',src=resized,alt='Still resizing...'),thing))
        else:
            raise Return((fid,d.img(class_='wid',src=thing,style=style),thing))
    # can't scale videos, so just adjust their width/height in CSS
    wrapper = None
    if type.startswith('audio') or type.startswith('video') or type == 'application/octet-stream':
        if type.endswith('webm') or type.endswith('ogg'):
            if type[0]=='a':
                wrapper = audio
            else:
                wrapper = video
            raise Return((fid,wrapper(source(src=thing,type=type),
                    d.object(
                        embed(src=thing,style=style,type=type),
                        width=width, height=height,
                        data=thing,style=style,type=type),
                        autoplay=True,loop=True),thing))
        else:
            raise Return((fid,(d.object(
                    embed(' ',src=thing,style=style,type=type,loop=True,autoplay=True),
                    d.param(name='src',value=thing),
                        style=style,
                        type=type,
                        loop=True,
                        autoplay=True,
                        width=width,
                        height=height),d.br(),"Download"),thing))
    if type == 'application/x-shockwave-flash':
        raise Return((fid,(d.object(d.param(name='SRC',value=thing),
                embed(' ',src=thing,style=style),
                style=style),d.br(),'Download'),thing))
    raise RuntimeError("What is "+type)

def mediaLink(id,type):
    return '/media/{:x}/{}'.format(id,type)

def simple(info,path,params):
    if Session.head: return
    id,type = info
    return makePage("derp",d.a(d.img(class_='wid',src=mediaLink(id,type)),href=pageLink(id)))

@gen.coroutine
def resized(info,path,params):
    id = int(path[1],0x10)
    while True:
        fid, exists = yield filedb.checkResized(id)
        if exists: break
    raise Redirect("/resized/"+fid+"/donotsave.this")

tagsModule = tags # sigh

def checkExplain(id,link,width,height,thing):
    style = [
            ('#img', {
                'width': str(width)+'px',
                'height': str(height)+'px',
                }),
            ('#img .exp', {
                            'position': 'absolute',
                }),
            ('#img .exp div', {
                'visibility': 'hidden',
                }),
            ('#img .exp:hover div', {
                            'visibility': 'visible',
                })]

    def getareas():
        for i,(aid,top,left,w,h,text) in enumerate(explanations.explain(id)):
            style.append(('#i'+str(i), {
                'top': top,
                'left': left,
                'width': w,
                'height': h,
            }))

            yield d.div(d.div(text),
                        {'class': 'exp',
                         'id': 'i'+str(i),
                         'data-id':aid})

    link = d.a(link,id='mediumu',href=thing)
    areas = tuple(getareas())
    if areas:
        imgmap = (makeStyle(style),)+areas
        return d.div(link,id='img',*imgmap)
    else:
        return d.div(link,id='img')

linepat = re.compile('[ \t]*\n+\s*')
    
def maybeDesc(id):
    blurb = db.execute('SELECT blurb FROM descriptions WHERE id = $1',(id,))
    if blurb:
        lines = linepat.split(blurb[0][0])
        avglen = min(120,max(40,mean(len(line) for line in lines)))
        return d.div([d.p(p) for p in lines],
                     style='width: {}em'.format(avglen/2),
                     id='desc')
    return None
    
@gen.coroutine
def page(info,path,params):
    if Session.head:
        id,modified,size = info
    else:
        id,next,prev,name,type,width,height,size,modified,tags,comic = info

    doScale = not 'ns' in params
    doScale = doScale and User.rescaleImages and size >= maxSize

    if Session.head:
        if doScale:
            fid, exists = yield filedb.checkResized(id)
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
    fid,link,thing = yield makeLink(id,type,name,doScale,width,height)
    tail = []
    def pageURL(id):
        return '../{:x}'.format(id)
    def updateComic(comic):
        def comicURL(id):
            return '/art/~comic/{:x}/'.format(id)
        comic, title, prev, next = comic
        if next:
            Links.next = pageURL(next)
        if prev:
            Links.prev = pageURL(prev);
        tail.append(d.p("Comic: ",d.a(title,href=comicURL(comic)),' ',d.a('<<',href=Links.prev) if prev else None,d.a('>>',href=Links.next) if next else None))
    with Links:
        if comic:
            updateComic(comic)
        if tags:
            tail.append(d.p("Tags: ",((' ',d.a(tag[0],id=tag[1],class_='tag',href=place+"/"+quote(tag[0]))) for tag in tags)))
        if next and not Links.next:
            Links.next = pageURL(next)+unparseQuery()
        if prev and not Links.prev:
            Links.prev = pageURL(prev)+unparseQuery()

        link = checkExplain(id,link,width,height,thing)
        page = makePage("Page info for "+fid,
                comment("Tags: "+boorutags),
                                        d.div(link),
                        maybeDesc(id),
                        d.p(d.a('Info',href=place+"/~info/"+fid)),
                        tail)
        raise Return(page)

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

@gen.coroutine
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
    fid,exists = yield filedb.check(id)
    Session.refresh = not exists
    tags = [str(tag) if not isinstance(tag,str) else tag for tag in info['tags']]
    info['tags'] = ', '.join(tags)

    page = makePage("Info about "+fid,
            d.p(d.a(d.img(src=thumbLink(id)),d.br(),"Page",href=pageLink(id))),
            d.table((d.tr(d.td(key),d.td(stringize(info[key]),id=key)) for key in keys),Class='info'),
            d.hr(),
            "Sources",
            d.span((d.p(d.a(source,href=source)) for id,source in sources),id='sources'))
    raise Return(page)


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

@gen.coroutine
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
        links = yield makeLinks(info)
        page = makePage("Media "+str(basic),
                d.p("You are ",d.a(User.ident,href=place+"/~user")),
                #d.table(makeLinks(info)),
                        d.div(links,id='thumbs') if links else '',
                (d.div("Related tags",d.hr(),doTags(url.path.rstrip('/'),related),id='related') if related else ''),
                (d.div("Remove tags",d.hr(),spaceBetween(removers),id='remove') if removers else ''),
                d.p((d.a('Prev',href=Links.prev),' ') if Links.prev else '',(d.a('Next',href=Links.next) if Links.next else '')))
        raise Return(page)

@gen.coroutine
def desktop(raw,path,params):
    import desktop
    if 'n' in params:
        n = int(params['n'][0],0x10)
    else:
        n = 0x10
    history = desktop.history(n)
    if not history:
        raise Return("No desktops yet!?")
    if 'd' in params:
        raise Redirect(pageLink(0,history[0]))
    if Session.head:
        Session.modified = db.execute("SELECT EXTRACT(EPOCH FROM modified) FROM media WHERE media.id = $1",(history[0],))[0][0]
        return
    if n == 0x10:
        current = history[0]
        history = history[1:]
        name,type,tags = db.execute("SELECT name,type,array(select name from tags where tags.id = ANY(neighbors)) FROM media INNER JOIN things ON things.id = media.id WHERE media.id = $1",(current,))[0]
        tags = [str(tag) for tag in tags]
        type = stripPrefix(type)
        middle = (
            d.p("Having tags ",doTags(place,tags)),
            d.p(d.a(d.img(class_='wid',src="/".join(("","media",'{:x}'.format(current),type,name))),
                href=pageLink(current,0))),
            d.hr())
    else:
        middle = ''
    @gen.coroutine
    def makeDesktopLinks():
        links = []
        allexists = True
        for id,name in db.execute("SELECT id,name FROM media WHERE id = ANY ($1::bigint[])",(history,)):
            fid,exists = yield filedb.check(id)
            allexists = allexists and exists
            links.append(d.td(d.a(d.img(title=name,src="/thumb/"+fid),
                            href=pageLink(id))))
        Session.refresh = not allexists
        raise gen.Return(links)
    links = yield makeDesktopLinks()
    def makeDesktopRows():
        row = []
        for td in links:
            row.append(td)
            if len(row) == 8:
                yield d.tr(row)
                row = []
        if len(row):
            yield d.tr(row)

    Session.modified = db.execute("SELECT EXTRACT (epoch from MAX(added)) FROM media")[0][0]
    page = makePage("Current Desktop",
            middle,
            d.p("Past Desktops"),
            d.div(
                d.table(
                    makeDesktopRows())))
    raise Return(page)


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
            result = db.execute("SELECT tags.name FROM tags WHERE id = ANY($1::bigint[])",(defaultTags.posi,))
            for name in result:
                yield name[0],False
            result = db.execute("SELECT tags.name FROM tags WHERE id = ANY($1::bigint[])",(defaultTags.nega,))
            for name in result:
                yield name[0],True
        result = makeResult()
    else:
        result = db.execute('SELECT tags.name,uzertags.nega FROM tags INNER JOIN uzertags ON tags.id = uzertags.tag WHERE uzertags.uzer = $1',(User.id,))
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
    return db.execute("SELECT type FROM media WHERE id = $1",(medium,))[0][0]

def getStuff(medium):
    return db.execute('''SELECT
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
    modified = db.execute('SELECT EXTRACT(EPOCH FROM modified) FROM media WHERE id = $1',(medium,))[0][0]
    if modified:
        if Session.modified:
            Session.modified = max(modified,Session.modified)
        else:
            Session.modified = modified

@gen.coroutine
def showAllComics(params):
    page = getPage(params)
    comics = comic.list(page,User.tags().nega)
    def getInfos():
        for id,title,tagids,tags in comics:
            try:
                medium = comic.findMedium(id,0)
            except Redirect:
                medium = 0x5c911
            if not medium:
                medium = 0x5c911
            checkModified(medium)
            yield medium,title,getType(medium),tags or ()
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
        links = yield makeLinks(getInfos(),formatLink)
        page = makePage("{:x} Page Comics".format(page),
                links if links else '',
                d.p((d.a("Prev",href=Links.prev) if Links.prev else ''),
                    (' ' if Links.prev and Links.next else ''),
                    (d.a("Next",href=Links.next)if Links.next else '')))
        raise Return(page)

@gen.coroutine
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
    title,description,source,tags = comic.findInfoDerp(com)[0]
    if not description: description = 'ehunno'
    def getInfos():
        for medium,which in getMedia():
            yield medium,title + ' page {}'.format(which),getType(medium),()
    with Links:
        if page > 0:
            Links.prev = unparseQuery({'p':page-1})
        if page + 1 < numPages:
            Links.next = unparseQuery({'p':page+1})
        links = yield makeLinks(getInfos(),lambda medium,i: '{:x}/'.format(i+offset))
        page = makePage(title + " - Comics",
                d.h1(title),
                links if numPages and links else '',
                d.p(RawString(description)),
                d.p("Tags:",", ".join(tags)),
                d.p(d.a('Source',href=source)) if source else '',
                d.p((d.a("Prev ",href=Links.prev) if Links.prev else ''),
                    d.a("Index",href=".."),
                    (d.a(" Next",href=Links.next)if Links.next else '')))
        raise Return(page)


@gen.coroutine
def showComicPage(path):
    com = int(path[0],0x10)
    which = int(path[1],0x10)
    medium = comic.findMedium(com,which)
    checkModified(medium)
    if Session.head: return
    title,description,source,tags = comic.findInfoDerp(com)[0]
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
        fid,link,thing = yield makeLink(medium,typ,name,
                doScale,style='width: 100%')
        link = checkExplain(medium,link,width,height,Links.next)
        page = makePage("{:x} page ".format(which)+title,
                d.div(link),
        maybeDesc(medium),
                d.p((d.a("Prev ",href=Links.prev) if Links.prev else ''),
                    d.a("Index",href=".."),
                    (d.a(" Next",href=Links.next)if Links.next else '')),
                d.p(d.a("Page",href="/art/~page/"+fid),(' ',d.a("Medium",href=link)) if doScale else None),
                        d.p("Tags: ",", ".join(tags)))
        raise Return(page)


def showComic(info,path,params):
    path = path[1:]
    if len(path) == 0:
        return showAllComics(params)
    elif len(path) == 1:
        return showPages(path,params)
    else:
        return showComicPage(path)

@gen.coroutine
def oembed(info, path, params):
    Session.type = 'application/json'
    if Session.head: return
    id,tags = info
    base = makeBase()
    xid, exists = yield filedb.check(id)
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
    raise Return(json.dumps(response))
