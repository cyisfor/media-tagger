import time
start =time.time()
import setupurllib
print('setupurllib imported in',time.time()-start)

import botkilla
import filedb # sigh...

from redirect import Redirect

import info
import note

from user import User,UserError

from dispatcher import dispatch,process
import uploader
import tagfilter
from dimensions import thumbnailPageSize

from session import Session

import pages,jsony
import withtags
import tags as tagsModule
from tags import Taglist

from eventlet.green.http.server import HTTPServer,BaseHTTPRequestHandler

from itertools import count
import urllib.parse
import sys
import os
oj = os.path.join

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
        if self.command != 'POST':
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
#	'fcd9:e703:498e:5d07:e5fc:d525:80a6:a51c' # heh
}

class Handler(FormCollector,BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    ip = None
    uploading_put = False
    uploader = None
    started = BaseHTTPRequestHandler.date_time_string(BaseHTTPRequestHandler,time.time())
    log = open(oj(filedb.top,"access.log"),"at")
    def recordAccess(self, *a, **kw):
        if not self.ip in IGNORED:
            return super().recordAccess(*a, **kw)
    def __init__(self,*a,**kw):
        BaseHTTPRequestHandler.__init__(self,*a,**kw)
        FormCollector.__init__(self,*a,**kw)
    def do_HEAD(self):
        with Session():
            Session.head = True
            return self.get()
    def do_GET(self):
        with Session():
            Session.head = False
            return self.get()
    def do_PUT(self):
        self.uploading_put = True
        self.upload()
    def do_POST(self):
        self.upload()
    def upload(self):
        note.shout('derp')
    botlog = open(oj(filedb.top,'bot.log'),'at')
    def botrespond(self):
        if not (self.ip in BOTS or self.path == '/art/bots/'): return False
        name,head,headwbody = botkilla.select(self.date_time_string(),self.ip)
        self.botlog.write(' '.join(name,self.ip,self.path))
        self.botlog.flush()
        if self.command.lower() == 'head':
            return self.wfile.write(head)
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
            note.red(id,name,ip,'sending a bit',
                     len(piece),'{}/{}'.format(i,pieces))
            self.wfile.write(piece)
            if len(piece) < blocksize: break
            time.sleep(0.1)
            note.red(id,name,ip,'done')
    def parse_request(self):
        ret = super().parse_request()
        note.shout("HEY",self.headers)
        if self.ip is None:
            if 'X-Real-Ip' in self.headers:
                self.ip = self.headers['X-Real-Ip']

            elif 'X-Forwarded-For' in self.headers:
                self.ip = self.headers['X-Forwarded-For']
                note('setting forw',value)
        if self.ip is not None:
            User.setup(self.ip)
        return ret
    def do_OPTIONS(self):
        self.send_response_only(200,"OK")
        self.send_header('Content-Length',0)
        self.send_header('Access-Control-Allow-Origin',"*")
        self.send_header('Access-Control-Allow-Methods',"GET,POST,PUT")
        self.send_header('Access-Control-Allow-Headers',
                         self.headers['access-control-request-headers'])
    def do_POST(self):
        json,path,parsed,params = parsePath(self.path)
        mode = path[0][1:]
        self.form.update(params)
        note(self.form)
        raise Redirect(process(mode,parsed,self.form,None))
    content_length = 0
    chunked = False
    def end_headers(self):
        if self.chunked:
            self.send_header('Transfer-Encoding','chunked')
        else:
            if Session.head:
                self.send_header('Content-Length',0)
            else:
                self.send_header('Content-Length',self.content_length)
            self.send_header('Transfer-Encoding','identity')
        return super().end_headers()
    def handle_one_request(self):
        try:
            with User():
                return super().handle_one_request()
        except Redirect:
            e = sys.exc_info()[1]
            note.shout('gode',repr(e.code))
            self.send_response(e.code,e.message)
            self.send_header('Location',e.location)
            self.send_header('Content-Length',0)
            self.end_headers()
    def get(self):
        json,path,pathurl,params = parsePath(self.path)
        Session.handler = self
        Session.params = params

        if len(path)>0 and len(path[0])>0 and path[0][0]=='~':
            mode = path[0][1:]
            page = dispatch(json,mode,path,params)
        else:
            Session.params = params
            implied = self.headers.get("X-Implied-Tags")
            if implied:
                tags = tagsModule.parse(implied,False)
            else:
                tags = tagsModule.parse("-special:rl",False)
            tags.update(User.tags())
            basic = Taglist()

            for thing in path:
                if thing:
                    thing = urllib.parse.unquote(thing)
                    bitt = tagsModule.parse(thing,False)
                    tags.update(bitt)
                    basic.update(bitt)
            tagfilter.filter(tags)
            print('effective tags',repr(tags))
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
                with disp.Links():
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

            if 'p' in params:
                pageSize = int(params['p'][0])
            else:
                pageSize = thumbnailPageSize
                
            def getPage():
                if 'q' in params:
                    try:
                        ident,name,ctype,ignoretags = next(withtags.searchForTags(
                            tags,
                            offset=o,
                            limit=1))
                    except StopIteration:						
                        if json:
                            return []
                        else:
                            @prevnext
                            def page():
                                disp.Links.next = None
                                return pages.makePage('No Results Found',
                                                      pages.d.p('No Results Found'))
                            return page
                    else:
                        @prevnext
                        def page():
                            return disp.page(
                                info.pageInfo(ident),path,params)
                            return page
                        return page
                else:
                    if o:
                        offset = pageSize*o
                    else:
                        offset = 0
                        
                    return disp.media(
                        pathurl,
                        params,
                        o,
                        pageSize,
                        withtags.searchForTags(
                            tags,
                            offset=offset,
                            limit=pageSize),
                        withtags.searchForTags(
                            tags,
                            offset=offset,
                            limit=pageSize,
                            wantRelated=True),
                        basic)
            with disp.Links():
                page = getPage()
        if json:
            Session.type = 'application/json'
            page = jsony.encode(page)
        else:
            #checkdirty.circular(page)
            page = str(page)
        page = page.encode('utf-8') + b'\n'
        self.send_response(200,"Okie Dokie Loki")
        self.send_header('Content-Type',
                         Session.type if Session.type else
                         'application/json; charset=utf-8' if json else
                         'text/html; charset=utf-8')
        if Session.modified:
            self.send_header('Last-Modified',
                             self.date_time_string(float(Session.modified)))		
        self.content_length = len(page)
        if Session.refresh:
            if Session.refresh is True:
                Session.refresh = 5
            self.send_header('Refresh',str(Session.refresh))
        self.end_headers()
        if not Session.head:
            self.wfile.write(page)
import socket
class MyServer(HTTPServer):
    address_family=socket.AF_INET6
print('OK waiting on http://[::1]:8029')
MyServer(('::1',8029),Handler).serve_forever()
