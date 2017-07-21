import eventlet
from eventlet.green.http.server import HTTPServer,BaseHTTPRequestHandler
from socketserver import _ServerSelector
import selectors

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

serv = HTTPServer(("127.0.0.1",14234),Handle)
with _ServerSelector() as selector:
	selector.register(serv,selectors.EVENT_READ)
	while True:
		ready = selector.select(None)
		if ready:
			serv._handle_request_noblock()
		serv.service_actions()

