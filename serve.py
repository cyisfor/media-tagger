from http.server import BaseHTTPRequestHandler,HTTPServer
from pages import images
import withtags
import db
import filedb
import urllib.parse

from dispatcher import dispatch

def parsePath(pathquery):
    from urllib.parse import urlparse,parse_qs
    parsed = urlparse(pathquery)
    params = parse_qs(parsed.query)
    return parsed,params

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        pathurl,params = parsePath(self.path)
        path = pathurl.path
        path = path.split('/')
        path = path[1:] # blank at the front
        if len(path)>0 and len(path[0])>0 and path[0][0]=='~':
            mode = path[0][1:]
            if len(path)>1:
                id = int(path[1],0x10)
            else:
                id = None
            page = dispatch(mode,id)
        else:
            tags = set()
            negatags = set()
            implied = self.headers.get("X-Implied-Tags")
            if implied:
                for thing in implied.split(','):
                    thing = thing.strip()
                    if thing[0] == '-':
                        tags.discard(thing[1:])
                        negatags.add(thing[1:])
                    else:
                        tags.add(thing)
            for thing in path:
                if thing:
                    thing = urllib.parse.unquote(thing)
                    if thing[0] == '-':
                        tags.discard(thing[1:])
                        negatags.add(thing[1:])
                        continue
                    elif thing[0] == '+':
                        thing = thing[1:]
                    tags.add(thing)
            o = params.get('o')
            if o:
                o = int(o[0],0x10)
                offset = 0x30*o
            else:
                offset = o = 0
            page = images(pathurl,params,o,
                    withtags.searchForTags(tags,negatags,offset=offset,limit=0x30))
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
        else:
            super(Server,self).handle_error(request,address)

Server(("127.0.0.1",8029),Handler).serve_forever()
