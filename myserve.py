import botkilla
from mytornado import sleep
import filedb # sigh...

import fix.tornado # SIGH...

from derp import printStack
#import checkdirty

import time
start =time.time()
import setupurllib
print('db imported in',time.time()-start)

import info
import myserver
import note

from user import User,UserError
import user
from redirect import Redirect
from dispatcher import dispatch,process
import uploader
import tagfilter
from dimensions import thumbnailPageSize

from setupurllib import isPypy

from session import Session

import pages,jsony
import withtags
import tags as tagsModule
from tags import Taglist

from tornado import gen, ioloop

from itertools import count
import urllib.parse

import os
oj = os.path.join

note.monitor(myserver)
note.monitor(__name__)

def parsePath(pathquery):
    parsed = urllib.parse.urlparse(pathquery)
    params = urllib.parse.parse_qs(parsed.query)
    path = parsed.path
    if path.endswith('.json'):
        json = True
        if not path.endswith('/.json'):
            path = path[:-len('.json')]+'/'
    elif not path.endswith('/'): 
        # we want a trailing / or can't tell whether to go . or ..
        raise Redirect(path + '/')
    else:
        json = False
    path = path.split('/')[:-1] # last is a blank for the trailing /
    path = path[2:] # blank, art at the front
    path = [urllib.parse.unquote(thing) for thing in path] # some sites make ~ -> %7E -_-
    return json,path,parsed,params

class FormCollector:
    form_data = False
    form = None
    request_body = None
    disabled = False
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        if self.method != 'POST':
            self.disabled = True
        else:
            self.chunks = []
    def data_received(self,chunk):
        if self.disabled: return super().data_received(chunk)
        if self.form_data:
            note('do something')
        else:
            self.chunks.append(chunk)
    def do(self):
        if self.disabled: return super().do()
        if not self.form_data:
            self.request_body = b''.join(self.chunks)
            self.form = {}
            if self.request_body:
                thing = self.request_body.decode('utf-8')
                thing = thing.split('&')
                thing = (i.split('=',1) for i in thing)
                self.parameters = ()
                self.form = {}
                uq = urllib.parse.unquote_plus
                for thing in thing:
                    if len(thing) == 2:
                        n,v = thing
                        n = uq(n)
                        v = uq(v)
                    else:
                        n = uq(thing[0])
                        v = True
                    self.parameters += ((n,v),)
                    vs = self.form.get(n)
                    if vs:
                        vs.append(v)
                    else:
                        self.form[n] = [v]
        return super().do()
    def received_header(self,name,value):
        if self.disabled: return super().received_header(name, value)
        if name != 'Content-Type': 
            return super().received_header(name,value)
        self.form_data = 'application/form-data' in value
        if self.form_data:
            note('form data')
            self.form = 'some mime thing'
        else:
            note('urlencoded')
            self.chunks = []
        return super().received_header(name,value)

IGNORED = {
    'fcd9:e703:498e:5d07:e5fc:d525:80a6:a51c'
}

BOTS = {
    'fce3:14aa:64d0:f72a:cb3f:6c04:3943:ffb6',
    'fcd9:8810:bb91:fd19:ddae:5c59:6df5:949e',
    'fc46:a72b:9577:4fdf:236d:3665:ee6a:3dcd',
#    'fcd9:e703:498e:5d07:e5fc:d525:80a6:a51c' # heh
}

class Handler(FormCollector,myserver.ResponseHandler):
    ip = None
    uploading_put = False
    uploader = None
    started = myserver.ResponseHandler.date_time_string(myserver.ResponseHandler,time.time())
    log = open(oj(filedb.top,"access.log"),"at")
    def recordAccess(self, *a, **kw):
        if not self.ip in IGNORED:
            return super().recordAccess(*a, **kw)
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        self.uploading_put = self.method == 'PUT'
    def received_headers(self):
        if self.ip is None:
            self.ip = self.conn.address[0]
        self.user = user.User(self.ip)
        if self.uploading_put:
            self.uploader = uploader.manage(self.user,self.length)
        #return super().received_headers()
    def data_received(self,data):
        if self.uploader: 
            self.uploader.data_received(data)
        else:
            return super().data_received(data)
    def received_header(self, name, value):
        if self.ip is None:
            if name == 'X-Real-Ip':
                note('setting real',value)
                self.ip = value
            elif name == 'X-Forwarded-For':
                note('setting forw',value)
                self.ip = value
        return super().received_header(name,value)
    @gen.coroutine
    def do(self):
        try:
            if self.uploader:
                yield self.send_status(301,"enjoy")
                media = yield self.uploader.result
                yield self.send_header('Location','/art/~page/{:x}'.format(media))
                return
            with self.user, Session:
                try: yield super().do() or myserver.success
                except Redirect as r:
                    yield self.send_status(r.code,"go")
                    yield self.send_header('Location',r.where)
        except UserError as e:
            print(e)
            yield self.send_status(500, "Ow")
            yield self.write(("Something blew up: "+str(e)).encode('utf-8'))
    def head(self):
        with Session:
            Session.head = True
            return self.get()
    @gen.coroutine
    def options(self):
        yield self.send_response(200,"OK")
        yield self.send_header('Content-Length',0)
        yield self.send_header('Access-Control-Allow-Origin',"*")
        yield self.send_header('Access-Control-Allow-Methods',"GET,POST,PUT")
        self.send_header('Access-Control-Allow-Headers',self.headers['access-control-request-headers'])
    def post(self):
        json,path,parsed,params = parsePath(self.path)
        mode = path[0][1:]
        self.form.update(params)
        note(self.form)
        raise Redirect(process(mode,parsed,self.form,None))
    botlog = open(oj(filedb.top,'bot.log'),'at')
    def respond(self):        
        if self.ip in BOTS or self.path == '/art/bots/':
            name,head,headwbody = botkilla.select(self.date_time_string(),self.ip)
            print(name,self.ip,self.path,file=self.botlog)
            self.botlog.flush()
            if self.method.lower() == 'head':
                return self.send_blob(head)
            @gen.coroutine
            def delaySender(id,name,ip,headwbody):
                block = 0x10
                blocksize = 1 << block
                pieces = int((headwbody.len >> block) + 1)
                assert pieces > 0, headwbody.len
                for i in range(pieces+1):
                    piece = headwbody.get(i << block,(i+1) << block)
                    if not headwbody.b:
                        note.red(id,name,ip,'LAOST')
                        break
                    if not piece:
                        note.cyan('too faaaaaar')
                        break
                    note.red(id,name,ip,'sending a bit',len(piece),'{}/{}'.format(i,pieces))
                    yield self.send_blob(piece)
                    if len(piece) < blocksize: break
                    yield sleep(0.1)
                note.red(id,name,ip,'done')
            self.timeout = None
            return delaySender('{:x}'.format(id(headwbody)),name,self.ip,headwbody)
        return super().respond()
    @gen.coroutine
    @printStack
    def get(self):
        Session.handler = self
        # meh
        # if self.path == '/art/~style':
        #     self.send_status(200,"Rainbow Dash")
        #     self.send_header('Content-Type',"text/css")
        #     self.send_header('Last-Modified',self.started)
        #     if Session.head:
        #         self.set_length(0)                    
        #     else:
        #         self.set_length(len(pages.style))
        #         self.write(pages.style)
        #     return            
        
        json,path,pathurl,params = parsePath(self.path)
        Session.params = params

        # Session.query = ...
        if len(path)>0 and len(path[0])>0 and path[0][0]=='~':
            mode = path[0][1:]
            page = yield gen.maybe_future(dispatch(json,mode,path,params))
        else:
            Session.params = params
            implied = self.headers.get("X-Implied-Tags")
            if implied:
                tags = tagsModule.parse(implied)
            else:
                tags = tagsModule.parse("-special:rl")
            tags.update(User.tags())
            basic = Taglist()

            for thing in path:
                if thing:
                    thing = urllib.parse.unquote(thing)
                    if thing[0] == '-':
                        tag = tagsModule.getTag(thing[1:])
                        if tag:
                            tags.posi.discard(tag)
                            tags.nega.add(tag)
                            basic.nega.add(tag)
                        continue
                    elif thing[0] == '+':
                        thing = thing[1:]
                    tag = tagsModule.getTag(thing)
                    if tag:
                        tags.posi.add(tag)
                        basic.posi.add(tag)
                        tags.nega.discard(tag)
            tagfilter.filter(tags)
            o = params.get('o')
            if o:
                o = int(o[0],0x10)
            else:
                o = 0

            if json:
                disp = jsony
            else:
                disp = pages
            def prevnext(f):
                with disp.Links:
                    if json:
                        disp.Links.next = o + 1
                    else:
                        params['o'] = o + 1
                        disp.Links.next = disp.unparseQuery(params)
                    if o > 0:
                        if json:
                            disp.Links.prev = o - 1
                        else:
                            params['o'] = o - 1
                            disp.Links.prev = disp.unparseQuery(params)
                    return f()
                
            def getPage():
                if 'q' in params:
                    try:
                        ident,name,ctype,ignoretags = next(withtags.searchForTags(tags,offset=o,limit=1))
                    except StopIteration:                        
                        if json:
                            return []
                        else:
                            @prevnext
                            def page():
                                disp.Links.next = None
                                return gen.maybe_future(
                                    pages.makePage('No Results Found',
                                                   pages.d.p('No Results Found')))
                            return page
                    else:
                        @prevnext
                        def page():
                            return gen.maybe_future(disp.page(
                                info.pageInfo(ident),path,params))
                            return page
                        return page
                else:
                    if o:
                        offset = thumbnailPageSize*o
                    else:
                        offset = 0
                        
                    return gen.maybe_future(disp.media(pathurl,params,o,
                            withtags.searchForTags(tags,offset=offset,limit=thumbnailPageSize),
                            withtags.searchForTags(tags,offset=offset,limit=thumbnailPageSize,wantRelated=True),basic))
            page = yield getPage()
        if json:
            Session.type = 'application/json'
            page = jsony.encode(page)
        else:
            #checkdirty.circular(page)
            page = str(page)
        page = page.encode('utf-8') + b'\n'
        self.send_status(200,"Okie Dokie Loki")
        self.send_header('Content-Type',Session.type if Session.type else 'application/json; charset=utf-8' if json else 'text/html; charset=utf-8')
        if Session.modified:
            self.send_header('Last-Modified',self.date_time_string(float(Session.modified)))        
        if Session.head:
            self.set_length(0)
        else:
           self.set_length(len(page))
        if Session.refresh:
            if Session.refresh is True:
                Session.refresh = 5
            self.send_header('Refresh',str(Session.refresh))
        self.end_headers()
        if not Session.head:
            self.write(page)

#myserver.Server(Handler).listen(8934)
myserver.Server(Handler).listen(8029,address='::1')
ioloop.IOLoop.instance().start()
