import tags,db,pages,create,filedb
tagsModule = tags
from user import User
from pages import d,RawString,Links

from replacer import replacerFile

import http.client as codes

import shutil,datetime
import email.utils
import os

def setup():
    db.setup('''CREATE TABLE uploads (    
    uzer INTEGER REFERENCES uzers(id) ON DELETE CASCADE ON UPDATE CASCADE,
    media bigint REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE,
    checked boolean DEFAULT FALSE)''',
    '''CREATE UNIQUE INDEX nodupesuploads ON uploads(uzer,media)''')

setup()

class Error(Exception): pass

def mycopy(src,dst,length=None):
    buf = bytearray(min(0x1000,length) if length else 0x1000)
    left = length
    while True:
        amt = src.readinto(buf)
        if amt <= 0: break
        dst.write(memoryview(buf)[:amt])
        if left is not None:
            left -= amt;
            if left < len(buf):
                buf = bytearray(left)

def manage(serv):
    message = 'Uploaded.'
    name = serv.headers.get('X-File-Name')
    checkderp = False
    if not name:
        name = serv.headers.get_filename()
        if not name:
            name = serv.path.rsplit('/',1)[-1]
            if not name:
                checkderp = True
                name = 'unknown.'+ magic.guess_extension(serv.headers.get_content_type())
    if not checkderp:
        if len(name)>0x80:
            raise Error("That file name is too long.")
        # what unicode characters shouldn't be allowed in names?
        # XXX: this will scramble the character order bleh
        # name = ''.join(set(name).intersection(goodCharacters))
        name = name.encode('utf-8').decode('utf-8')

    sources = serv.headers.get_all('X-Source',())
    if sources:
        primarySource = sources[0]
    else:
        primarySource = None
    
    tags = serv.headers.get('X-Tags')
    if tags:
        tags = tagsModule.parse(tags)
    else:
        tags = ()
    for bit in serv.headers.get_all('X-Tag',()):
        if bit:            
            bit = tagsModule.parse(bit)
            if tags:
                tags.update(bit)
            else:
                tags = bit

    media = None

    length = serv.headers.get('Content-Length')
    if length is not None:
        try: length = int(length)
        except ValueError: pass
        if length == 0:
            media = serv.headers.get("X-ID")
            if media:
                try:
                    media = int(media,0x10)
                except ValueError: 
                    try:
                        media = int(media)
                    except ValueError:
                        raise Error("X-ID must be an integer")
            else:
                raise Error("Either upload a file or provide an X-ID header")
    else:
        if serv.headers.get('Transfer-Encoding') == 'chunked':
            raise Error("Please don't use chunked transfer encoding!")
        raise Error("Your client didn't set the Content-Length header for some reason.")

    if media is None:
        def download(dest):
            mycopy(serv.rfile,dest,length)
            assert(dest.tell()>0)
            modified = serv.headers['Last-Modified']
            if modified is None:
                modified = serv.headers.get('If-Modified-Since')
            if modified is None:
                modified = datetime.datetime.now()
            else:
                modified = email.utils.parsedate(modified)
                modified = datetime.datetime(*(modified[:6]))
            if hasattr(modified,'timestamp'):
                timestamp = modified.timestamp()
            else:
                import time
                timestamp = time.mktime(modified.timetuple())
            os.utime(dest.name,(timestamp,timestamp))
            dest.seek(0,0)
            return modified    
        media = create.internet(download,primarySource,tags,primarySource,sources,name)
    else:
        result = db.c.execute("SELECT id FROM media WHERE id = $1",(media,))
        if not result:
            raise Error("No media by that ID")
        create.update(media,sources,tags)

    filedb.checkResized(media)
    if len(db.c.execute("SELECT uzer FROM uploads WHERE media = $1",(media,))) == 0:
        db.c.execute("INSERT INTO uploads (uzer,media) VALUES ($1,$2)",
            (User.id,media))
        db.retransaction();
        message = 'Uploaded '+name+' to your queue for tagging.'
    else:
        message = 'You already seem to have uploaded this.'

    message = (message+'\r\n').encode('utf-8')
    serv.send_response(codes.OK,"yay")
    serv.send_header("Content-Length",len(message))
    serv.end_headers()
    serv.wfile.write(message)

def page(info,path,params):
    def contents():
        first = True
        for media, in db.c.execute('SELECT media FROM uploads WHERE uzer = $1 and checked = FALSE',(User.id,)):
            name,type,tags,sources = db.c.execute('''SELECT
            name,type,
            array(select name from tags where id = ANY(things.neighbors) ORDER BY name),
            array(select uri from urisources where id = ANY(media.sources) ORDER BY uri)
        FROM media
        INNER JOIN things ON media.id = things.id
        LEFT OUTER JOIN images ON images.id = media.id
    WHERE media.id = $1''',(media,))[0]
            media = filedb.checkResized(media)
            
            location = '/resized/'+media+'/donotsave.this'
            if first:
                first = False
            else:
                yield d.hr()
            yield d.p(media,d.br(),d.form(
                d.input(name='media',value=media,type='hidden'),
                d.input(name='type',value=type,type='hidden'),
                d.a(d.img(src=location,alt='Still resizing...'),href='/art/~page/'+media),
                    d.div(
                        "Tags",
                        d.input(id='tags',name='tags',type='entry',value=', '.join(tags))),
                    d.div(
                        "Sources",
                        d.textarea(RawString('\n'.join(sources)),name="sources")),
                    d.div(d.button("Update")),
                    enctype='multipart/form-data',
                    method='POST'))
    with Links:
        Links.style = "/style/upload.css"
        return pages.makePage('Pending uploads',contents())

def addInfoToMedia(form):
    media = form.get('media')
    if not media: return
    dertags = form.get('tags')
    if not dertags: return
    sources = form.get('sources')    
    if not sources: return
    mime = form.get('type')
    # XXX: should do something with type
    if not mime: return
    dertags = tags.parse(dertags[0])
    media = int(media[0],0x10)
    sources = sources[0].split('\n')    

    with db.transaction():
        db.c.execute('UPDATE things SET neighbors = array(SELECT unnest(neighbors) UNION SELECT unnest($2::bigint[]) EXCEPT SELECT unnest($3::bigint[])) WHERE id = $1',
                (media,dertags.posi,dertags.nega))
        derp = []
        for source in sources:
            operation = 'UNION'
            if source and source[0] == '-':
                operation = 'EXCEPT'
                source = source[1:]
            derp.append(create.sourceId(source))
        db.c.execute("UPDATE media SET sources = array(SELECT unnest(sources) "+operation+" SELECT unnest($1::bigint[])) WHERE id = $2",(derp,media))
        db.c.execute("UPDATE uploads SET checked = TRUE WHERE uzer = $1 AND media = $2",(User.id,media))

def doPost(path,form):
    addInfoToMedia(form)
    return '/art/~uploads'