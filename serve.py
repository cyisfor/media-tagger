#!/usr/bin/env pypy3

#import preforking

from user import User,UserError
import user
from redirect import Redirect
from dispatcher import dispatch,process
import uploader
import tagfilter
from dimensions import thumbnailPageSize

from setupurllib import isPypy

from session import Session

import pages
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

import socket
import urllib.parse
from urllib.parse import urlparse,parse_qs
import io
import time
import sys
import os

debugging = 'debug' in os.environ

def encodeDict(d):
    for n,v in d.items():
        d[n] = v.encode('utf-8')

def decodeDict(d):
    newd = {}
    for n,v in d.items():
        newd[n.decode('utf-8')] = [vv.decode('utf-8') for vv in v]
    return newd

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
    def version_string(self):
        return 'MYOB/1.0'
    def fail(self,message):
        raise UserFailure(message)
    def log_message(self,format,*args):
        if not debugging and self.ip == 'fc1b:3f1e:dc7f:952a:f8e7:62c6:85cb:d7ea': return
        sys.stderr.write(("{} {} {} ({}) ".format(self.ip,self.command,self.path,time.time()))+
                (format%args)+'\n')
        sys.stderr.flush()
    def handle_one_request(self):
        try:
            self.raw_requestline = self.rfile.readline(0x10001)
            if len(self.raw_requestline) > 0x10000:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(414)
                return
            if not self.raw_requestline:
                self.close_connection = 1
                return
            if not self.parse_request():
                # An error code has been sent, just exit
                return
            self.do()
            self.wfile.flush()            
        except socket.timeout as e:
            self.log_error("Request timed out")
            self.close_connection = 1
            return
        except socket.error as e:
            import errno
            if e.errno == errno.EPIPE:
                self.log_error("Client closed connection")
                self.close_connection = 1
            else:
                raise
        except Exception as e:
            import traceback
            traceback.print_exc()
            if e.args:
                e = e.args[0]
            else:
                e = str(e)
            self.send_error(500,e)
            self.log_error(e)
            return

    def do(self):
        self.ip = self.headers.get('X-Real-IP')
        if not self.ip:
            self.ip = self.headers['X-Forwarded-For']
        mname = 'do_' + self.command
        if not hasattr(self, mname):
            self.send_error(501, "Unsupported method (%r)" % self.command)
            return
        method = getattr(self, mname)
        with user.being(self.headers['X-Real-IP']), Session:
            try: method()
            except Redirect as r:
                self.send_response(r.code,"go")
                self.send_header("location",r.where)
                self.end_headers()
            except UserError as e:   
                self.send_error(500,e.message)
                return
            except Exception as e:
                print('um',e)
                raise
    def do_OPTIONS(self):
        self.send_response(200,"OK")
        self.send_header('Content-Length',0)
        self.send_header('Access-Control-Allow-Origin',"*")
        self.send_header('Access-Control-Allow-Methods',"GET,POST,PUT")
        self.send_header('Access-Control-Allow-Headers',self.headers['access-control-request-headers'])
        self.end_headers()
    def do_PUT(self):
            try: uploader.manage(self)
            except uploader.Error as e:
                e = str(e)
                self.send_error(500,e)
    def do_POST(self):
        if not self.headers.get('Connection','') == 'close':
            print("WARN connection won't close!")
        path,parsed,params = parsePath(self.path)
        mode = path[0][1:]
        ctype, pdict = cgi.parse_header(self.headers['content-type'])
        length = int(self.headers.get('Content-Length'))

        if ctype != 'multipart/form-data':
            pdict = cgi.parse_qs(self.rfile.read(length))
            if isPypy:
                pdict = decodeDict(pdict)
            params.update(pdict)
            location = process(mode,parsed,params,None)
        else:
            boundary = pdict['boundary']
            if hasattr(boundary,'decode'):
                pdict['boundary'] = boundary.decode()
            if not isPypy:
                encodeDict(pdict) # sigh

            parts = self.rfile.read(length).split(boundary)
            location = process(mode,parsed,params,parts)
        
        self.send_response(codes.FOUND,"go")
        self.send_header("Location",location)
        self.end_headers()
    def do_HEAD(self):
        Session.head = True
        return self.do_GET()
    def do_GET(self):
        Session.handler = self
        path,pathurl,params = parsePath(self.path)
        Session.params = params
        # Session.query = ...
        if len(path)>0 and len(path[0])>0 and path[0][0]=='~':
            mode = path[0][1:]
            page = dispatch(mode,path,params)
        else:
            implied = self.headers.get("X-Implied-Tags")                
            if implied:
                tags = tagsModule.parse(implied)
            else:
                tags = tagsModule.parse("-special:rl")
            tagfilter.filter(tags)
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
            if 'q' in params:
                if o:
                    o = int(o[0],0x10)
                else:
                    o = 0
                ident,name,type,tags = next(withtags.searchForTags(tags,offset=o,limit=1))
                with pages.Links:
                    params['o'] = o + 1
                    pages.Links.next = pages.unparseQuery(params)
                    if o > 0:
                        params['o'] = o - 1
                        pages.Links.prev = pages.unparseQuery(params)
                    page = pages.page((ident,None,None,name,type,0,0,0,0,tags),path,params)
            else:
                if o:
                    o = int(o[0],0x10)
                    offset = thumbnailPageSize*o
                else:
                    offset = o = 0
                    
                page = images(pathurl,params,o,
                        withtags.searchForTags(tags,offset=offset,limit=thumbnailPageSize),
                        withtags.searchForTags(tags,offset=offset,limit=thumbnailPageSize,wantRelated=True),basic)
        page = str(page).encode('utf-8')
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
        if Session.head is False:
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
print('OK')
Server(("127.0.0.1",8029),Handler).serve_forever()
