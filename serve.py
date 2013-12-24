from http.server import BaseHTTPRequestHandler,HTTPServer
import http.client as codes
import cgi
from user import User
import user

from pages import images
import withtags
import db
import filedb
import urllib.parse
from urllib.parse import urlparse,parse_qs

import user
from redirect import Redirect
from dispatcher import dispatch,process

class UserFailure(Exception): pass

def parsePath(pathquery):
    parsed = urlparse(pathquery)
    params = parse_qs(parsed.query)
    path = parsed.path
    path = path.split('/')
    path = path[2:] # blank, art at the front
    return path,parsed,params

class Handler(BaseHTTPRequestHandler):
    def fail(self,message):
        self.send_error(message)
        raise UserFailure(message)
        with user.being(self.headers['X-Real-IP']):
    def do_POST(self):
        with user.being(self.headers["X-Real-IP"]):
            path,parsed,derparams = parsePath(self.path)
            mode = path[0][1:]
            ctype, pdict = cgi.parse_header(self.headers['content-type'])
            if ctype != 'multipart/form-data':
                self.fail("You can only post form data!")
            boundary = pdict['boundary']
            if hasattr(boundary,'encode'):
                pdict['boundary'] = boundary.encode()
            print(pdict)
            params = cgi.parse_multipart(self.rfile, pdict)
            location = process(mode,parsed,params)
            self.send_response(codes.FOUND,"go")
            self.send_header("location",location)
            self.end_headers()
    def do_GET(self):
        with user.being(self.headers["X-Real-IP"]):
            path,pathurl,params = parsePath(self.path)
            if len(path)>0 and len(path[0])>0 and path[0][0]=='~':
                mode = path[0][1:]
                try:
                    page = dispatch(mode,path,params)
                except Redirect as r:
                    self.send_response(r.code,"go")
                    self.send_header("location",r.where)
                    self.end_headers()
                    return
            else:
                tags = set()
                negatags = set()
                implied = self.headers.get("X-Implied-Tags")                
                if implied:
                    tags,negatags = withtags.parse(implied)
                tags.update(User.tags())
                negatags.update(User.tags(True))

                for thing in path:
                    if thing:
                        thing = urllib.parse.unquote(thing)
                        if thing[0] == '-':
                            tag = withtags.getTag(thing[1:])
                            tags.discard(tag)
                            negatags.add(tag)
                            continue
                        elif thing[0] == '+':
                            thing = thing[1:]
                        tag = withtags.getTag(thing)
                        tags.add(tag)
                o = params.get('o')
                if o:
                    o = int(o[0],0x10)
                    offset = 0x30*o
                else:
                    offset = o = 0
                print(tags,negatags)
                page = images(pathurl,params,o,
                        withtags.searchForTags(tags,negatags,offset=offset,limit=0x30),
                        withtags.searchForTags(tags,negatags,offset=offset,limit=0x30,wantRelated=True),tags,negatags)
            page = str(page).encode('utf-8')
            self.send_response(200,"OK")
            self.send_header('Content-Type','text/html; charset=utf-8')
            modified = db.c.execute("SELECT EXTRACT (epoch from MAX(added)) FROM media")[0][0]
            self.send_header('Last-Modified',self.date_time_string(float(modified)))
            self.send_header('Content-Length',len(page))
            self.end_headers()
            self.wfile.write(page)

class Server(HTTPServer):
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
        elif type == UserFailure:
            print('{}: {}'.format(client,ex),file=sys.stderr)
            return
        else:
            super(Server,self).handle_error(request,address)

Server(("127.0.0.1",8029),Handler).serve_forever()
