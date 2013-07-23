import dirty.html as d
from dirty import RawString
def comment(s):
    return RawString('<!-- '+s+' -->')
from place import place
from itertools import count
import fixprint

import user as herp
from obj import obj
from db import c
from redirect import Redirect
import filedb

from urllib.parse import quote as derp

import textwrap

maxWidth = 800

def wrappit(s):
    return textwrap.fill(s,width=0x40)

def quote(s):
    try:
        return derp(s).replace('/','%2f')
    except:
        print(repr(s))
        raise

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

def makeLinks(info):
    counter = count(0)
    row = []
    for id,name,type,tags in info:
        if next(counter)%8==0:
            if row:
                yield d.tr(*row)
            row = []
        tags = [str(tag) for tag in tags]
        if type == 'application/x-shockwave-flash':
            id = '%x'%(id)
            src = '/flash.jpg'
        else:
            id = filedb.check(id)
            src='/thumb/'+id
        type = stripPrefix(type)
        row.append(d.td(d.a(d.img(src=src,alt="...",title=name,href=place+'/~page/'+id),d.br(),d.sup('...',title=wrappit(', '.join(tags))) if tags else '???',href=place+'/~page/'+id)))
    if row: yield d.tr(*row)

links = obj(
    next=None,
    prev=None,
    query=None,
    params={},
    style="/style/art.css")

def standardHead(title,*contents):
    if links.params:
        params = []
        for name,values in links.params.items():
            for value in values:
                params.append(name+'='+quote(value))
        params = '?' + '&'.join(params)
    else:
        params = ''
    return d.head(d.title(title),
        d.link(rel='stylesheet',type='text/css',href=links.style),
        d.link(rel='next',href=links.next+params) if links.next else None,
        d.link(rel='prev',href=links.prev+params) if links.prev else None,
        *contents)

def makePage(title,*content):
    content = content + (
        d.p(d.a("User Settings",href=("/art/~user"))),)
    return d.xhtml(standardHead(title),d.body(*content))

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
        return None
    if type.startswith('image'):
        attrs = {'src': thing,
                'alt': 'Still resizing...'}
        if width and width>maxWidth:
            attrs['width'] = maxWidth
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


def page(info,path,params):
    id,next,prev,name,type,width,tags = info
    if name:
        name = name.split('?')[0]
        if not '.' in name:
            name = name + '/untitled.jpg'
    else:
        name = 'untitled.jpg'
    tags = [str(tag) if not isinstance(tag,str) else tag for tag in tags]
    tags = [degeneralize(tag) for tag in tags]
    boorutags = " ".join(tag.replace(' ','_') for tag in tags)
    guy = herp.currentUser()
    print("Got guy",guy)
    if guy['rescaleImages'] and width and width > maxWidth and not 'ns' in params:
        fid = filedb.checkResized(id,type,800)
        thing = '/resized/'+fid+'/donotsave.this'
    else:
        fid = '{:x}'.format(id)
        thing = '/'.join(('/image',fid,type,name))
    if tags:
        tagderp = d.p("Tags: ",((' ',d.a(tag,href=place+"/"+tag)) for tag in tags))
    else:
        tagderp = ''
    thing = makeLink(type,thing,width)
    with links:
        links.params = params
        if next:
            links.next = '{:x}'.format(next)
        if prev:
            links.prev = '{:x}'.format(prev)
        return makePage("Page info for "+fid,
                comment("Tags: "+boorutags),
                d.p(d.a(thing,href='/'.join(('/image',fid,type,name)))),
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
    import info as derp
    id = '{:x}'.format(info['id'])
    sources = [(id,derp.source(id)) for id in info['sources']]
    sources = [pair for pair in sources if pair[1]]
    print(sources)
    return makePage("Info about "+id,
            d.p(d.a(d.img(src="/thumb/"+id),d.br(),"Page",href=place+"/~page/"+id)),
            d.table((d.tr(d.td(key),d.td(stringize(info[key]))) for key in info.keys() if key != "sources" and key != "id"),Class='info'),
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
    return set([tag.replace('general:','') for tag in tags])

def images(url,query,offset,info,related,tags,negatags):
    related = [str(tag) for tag in related]
    related=stripGeneral(related)
    query['o'] = ['{:x}'.format(offset+1)]
    info = list(info)

    removers = []
    for tag in tags:
        removers.append(d.a(tag,href=tagsURL(tags.difference(set([tag])),negatags)))
    for tag in negatags:
        removers.append(d.a(tag,href=tagsURL(tags,negatags.difference(set([tag])))))

    with links:
        if len(info)>=0x30:
            links.next = url.path+'?'+unparseQuery(query)
        if offset != 0:
            query['o'] = ['{:x}'.format(offset-1)]
            links.prev = url.path+('?'+unparseQuery(query) if offset > 1 else '')
        return makePage("Images",
                d.p("You are ",d.a(herp.currentUser()['ident'],href="/art/~user")),
                d.table(makeLinks(info)),
                (d.p("Related tags",d.hr(),doTags(url.path.rstrip('/'),related)) if related else ''),
                (d.p("Remove tags",d.hr(),spaceBetween(removers)) if removers else ''),
                d.p((d.a('Prev',href=links.prev),' ') if links.prev else '',(d.a('Next',href=links.next) if links.next else '')))

def desktop(raw,path,params):
    import desktop
    history = desktop.history()
    if not history:
        return "No desktops yet!?"
    if 'd' in params:
        raise Redirect("/".join((place,"~page",'{:x}'.format(history[0]))))
    current = history[0]
    history = history[1:]
    for id in history:
        filedb.check(id)
    name,type,tags = c.execute("SELECT name,type,array(select name from tags where tags.id = ANY(neighbors)) FROM media INNER JOIN things ON things.id = media.id WHERE media.id = $1",(current,))[0]
    tags = [str(tag) for tag in tags]
    type = stripPrefix(type)
    named = c.execute("SELECT id,name FROM media WHERE id = ANY ($1::bigint[])",(history,))
    return makePage("Current Desktop",
            d.p("Having tags ",doTags(place,tags)),
            d.p(d.a(d.img(src="/".join(("","image",'{:x}'.format(current),type,name))),
                href=("/".join((place,"~page",'{:x}'.format(current)))))),
            d.hr(),
            d.p("Past Desktops"),
            d.div(
                d.table(
                    d.tr(
                        [d.td(d.a(d.img(title=name,src="/thumb/"+'{:x}'.format(id),alt=name),
                            href=place+"/~page/"+'{:x}'.format(id))) for id,name in named]))))

def user(info,path,params):
    self = herp.currentUser()
    iattr = {
            'type': 'checkbox',
            'name': 'rescale'}
    if self.get('rescaleImages'):
        iattr['checked'] = True
    rescalebox = d.input(iattr)
    return makePage("User Settings",
        d.form(
        d.ul(
            d.li("Rescale Images? ",rescalebox),
            d.li(d.input(type="submit",value="Submit"))),
        method="post",
        enctype="multipart/form-data"))
