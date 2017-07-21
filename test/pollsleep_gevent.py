from gevent import monkey, sleep
monkey.patch_all()

from http.server import HTTPServer,BaseHTTPRequestHandler
#import socketserver
#socketserver._ServerSelector = selectors.SelectSelector

def later():
	print("ummm")
	sleep(3)
	print("why is this never called?")

# make sure something hanging listening on 14234

gevent.spawn(later)

class Handle(BaseHTTPRequestHandler):
	def do_GET(self):
		print("get got")
		self.send_response(997,"boop")

serv = HTTPServer(("127.0.0.1",14234),Handle).serve_forever(None)
