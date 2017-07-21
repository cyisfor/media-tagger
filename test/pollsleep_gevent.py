import eventlet
from eventlet.green import selectors
import sys
sys.modules['selectors'] = selectors # SIGH
print(dir(selectors))
from eventlet.green.http.server import HTTPServer,BaseHTTPRequestHandler
import socketserver
socketserver._ServerSelector = selectors.SelectSelector

def later():
	print("ummm")
	eventlet.sleep(3)
	print("why is this never called?")

# make sure something hanging listening on 14234

eventlet.spawn_n(later)

class Handle(BaseHTTPRequestHandler):
	def do_GET(self):
		print("get got")
		self.send_response(997,"boop")

serv = HTTPServer(("127.0.0.1",14234),Handle).serve_forever(None)
