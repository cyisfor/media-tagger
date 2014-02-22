#import preforking

from user import User,UserError
import user
from redirect import Redirect
from dispatcher import dispatch,process
import uploader

from session import Session

from pages import images
import withtags
import tags as tagsModule
from tags import Taglist
import db
import filedb

from socketserver import ThreadingMixIn
from http.server import BaseHTTPRequestHandler,HTTPServer
import http.client as codes
import cgi

import urllib.parse
from urllib.parse import urlparse,parse_qs
import io
import time
import sys

def encodeDict(d):
    for n,v in d.items():
        d[n] = v.encode('utf-8')

def parsePath(pathquery):
    parsed = urlparse(pathquery)
    params = parse_qs(parsed.query)
    path = parsed.path
    if not path.endswith('/'): 
        # we want a trailing / or can't tell whether to go . or ..
        raise Redirect(path + '/')
    path = path.split('/')[:-1] # last is a blank for the trailing /
    path = path[2:] # blank, art at the front
    path = [urllib.parse.unquote(thing) for thing in path] # some sites make ~ -> %7E -_-
    return path,parsed,params

class Handler(BaseHTTPRequestHandler):
    def fail(self,message):
        raise UserFailure(message)
    def log_message(self,format,*args):
        sys.stderr.write(("%s %s %s (%s) "%(self.headers['X-Real-IP'],self.command,self.path,time.time()))+(format%args)+'\n')
        sys.stderr.flush()
    def do_OPTIONS(self):
        self.send_response(200,"OK")
        self.send_header('Content-Length',0)
        self.send_header('Access-Control-Allow-Origin',"*")
        self.send_header('Access-Control-Allow-Methods',"GET,POST,PUT")
        self.send_header('Access-Control-Allow-Headers',self.headers['access-control-request-headers'])
        self.end_headers()
    def do_PUT(self):
        with user.being(self.headers['X-Real-IP']):
            try: uploader.manage(self)
            except uploader.Error as e:
                e = str(e)
                self.send_response(500,e)
                self.end_headers()
                e += '\r\n'
                self.wfile.write(e.encode('utf-8'))
            except Redirect as r:
                self.send_response(r.code,"go")
                self.send_header("location",r.where)
                self.end_headers()
            except UserError as e:   
                self.send_error(500,e.message)
                return
    def do_POST(self):
        assert(self.headers.get('Connection','') == 'close')
        with user.being(self.headers["X-Real-IP"]):
            try:
                path,parsed,derparams = parsePath(self.path)
                mode = path[0][1:]
                ctype, pdict = cgi.parse_header(self.headers['content-type'])
                if ctype != 'multipart/form-data':
                    self.fail("You can only post form data!")
                boundary = pdict['boundary']
                if hasattr(boundary,'decode'):
                    pdict['boundary'] = boundary.decode()
                length = int(self.headers.get('Content-Length'))
                data = self.rfile.read(length)
                encodeDict(pdict) # sigh
                params = cgi.parse_multipart(io.BytesIO(data), pdict)
                location = process(mode,parsed,params)
            except Redirect as r:
                # this is kinda pointless...
                self.send_response(r.code,"go")
                self.send_header("location",r.where)
                self.end_headers()
                return
            except UserError as e:   
                self.send_error(500,e.message)
                return
            self.send_response(codes.FOUND,"go")
            self.send_header("location",location)
            self.end_headers()
    def do_GET(self):
        with user.being(self.headers["X-Real-IP"]), Session:            
            Session.handler = self
            try:
                path,pathurl,params = parsePath(self.path)
                Session.params = params
                # Session.query = ...
                if len(path)>0 and len(path[0])>0 and path[0][0]=='~':
                    mode = path[0][1:]
                    page = dispatch(mode,path,params)
                else:
                    tags = Taglist()
                    implied = self.headers.get("X-Implied-Tags")                
                    if implied:
                        tags = tagsModule.parse(implied)
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
                    o = params.get('o')
                    if o:
                        o = int(o[0],0x10)
                        offset = 0x30*o
                    else:
                        offset = o = 0
                    #withtags.explain = True
                    #withtags.searchForTags(tags,offset=offset,limit=0x30,wantRelated=True)
                    page = images(pathurl,params,o,
                            withtags.searchForTags(tags,offset=offset,limit=0x30),
                            withtags.searchForTags(tags,offset=offset,limit=0x30,wantRelated=True),basic)
                page = str(page).encode('utf-8')
            except Redirect as r:
                self.send_response(r.code,"go")
                self.send_header("location",r.where)
                self.end_headers()
                return
            except UserError as e:   
                self.send_error(500,e.message)
                return
            self.send_response(200,"OK")
            self.send_header('Content-Type',Session.type if Session.type else 'text/html; charset=utf-8')
            if Session.modified:
                self.send_header('Last-Modified',self.date_time_string(float(Session.modified)))
            self.send_header('Content-Length',len(page))
            if Session.refresh:
                if Session.refresh is True:
                    Session.refresh = 5
                self.send_header('Refresh',str(Session.refresh))
            self.end_headers()
            self.wfile.write(page)

Handler.responses[500] = 'Error','Server derped'
class Server(HTTPServer,ThreadingMixIn):
    def handle_error(self,request,address):
        import sys
        type,value,traceback = sys.exc_info()
        if type == SystemExit:
            self.shutdown_request(request)
            import threading # sigh...
            class Derp(threading.Thread):
                server=self
                def run(self):
                    self.server.shutdown()
            t = Derp()
            t.setDaemon(True)
            t.start()
            return
        elif type == UserError:
            return
        else:
            super(Server,self).handle_error(request,address)
            
#preforking.serve_forever(lambda: Server(("127.0.0.1",8029),Handler))
Server(("127.0.0.1",8029),Handler).serve_forever()
