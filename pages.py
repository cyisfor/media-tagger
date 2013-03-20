import dirty.html as d
from place import place

import filedb

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

def links(info):
    for id,name,type,tags in info:
        # shiiit
        tags = [str(tag) for tag in tags]
        type = stripPrefix(type)
        id = filedb.check(id)
        yield ' '
        yield d.a(d.img(src='/thumb/'+id,title=','.join(tags) if tags else '???'),href=place+'/~page/'+id)

def standardHead(title,*contents):
    return d.head(d.title(title),
        d.link(rel='stylesheet',type='text/css',href='/style/art.css'),
        *contents)

def makePage(title,*content):
    return d.xhtml(standardHead(title),d.body(*content))

maxWidth = 800

def page(info):
    id,name,type,width,tags = info
    tags = [str(tag) if not isinstance(tag,str) else tag for tag in tags]
    tags = [degeneralize(tag) for tag in tags]
    type = stripPrefix(type)
    if width > maxWidth:
        id = filedb.checkResized(id,type,800)
        thing = '/resized/'+id+'/donotsave.this'
    else:
        id = '{:x}'.format(id)
        thing = '/'.join(('/image',id,type,name))
    if tags:
        print(tags)
        tagderp = d.p("Tags: ",((' ',d.a(tag,href=place+"/"+tag)) for tag in tags))
    else:
        tagderp = ''
    return makePage("Page info for "+id,
            d.p(d.a(d.img(src=thing),href='/'.join(('/image',id,type,name)))),
            d.p(d.a('Info',href=place+"/~info/"+id)),
            tagderp)

def stringize(key):
    if hasattr(key,'isoformat'):
        return key.isoformat()
    elif isinstance(key,str):
        return key
    elif isinstance(key,bytes):
        return key.decode('utf-8')
    return str(key)

def info(info):
    print(info)
    id = '{:x}'.format(info['id'])
    return makePage("Info about "+id,
            d.p(d.a(d.img(src="/thumb/"+id),d.br(),"Page",href=place+"/~page/"+id)),
            d.table((d.tr(d.td(key),d.td(stringize(info[key]))) for key in info.keys() if key != "sources" and key != "id"),Class='info'),
            d.hr(),
            "Sources",
            (d.p(d.a(source,href=source)) for source in info['sources']))


def like(info):
    return "Under construction!"

def unparseQuery(query):
    return '&'.join(tuple('&'.join((n+'='+vv) for vv in v) for n,v in query.items()))

def images(url,query,offset,info):
    print('{:x}'.format(offset+1))
    query['o'] = ['{:x}'.format(offset+1)]
    nextURI = place+url.path+'?'+unparseQuery(query)
    if offset == 0:
        prevURI = None
    else:
        query['o'] = ['{:x}'.format(offset-1)]
        prevURI = place+url.path+('?'+unparseQuery(query) if offset > 1 else '')
    return d.xhtml(standardHead("Images",
            (d.link(rel='prev',href=prevURI) if prevURI else None),
            d.link(rel='next',href=nextURI)),
        d.body(d.p(links(info)),d.p((d.a('Prev',href=prevURI),' ') if prevURI else '',d.a('Next',href=nextURI))))
