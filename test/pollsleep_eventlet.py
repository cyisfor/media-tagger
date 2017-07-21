import eventlet
from eventlet.green import HTTPServer,BaseHTTPRequestHandler

def connectandhang():
    c = socket.socket()
    ip = socket.gethostbyname("localhost")
    c.connect((ip, 14234))
    return c.recv(1024)

def later():
	print("ummm")
	eventlet.sleep(3)
	print("why is this never called?")

# make sure something hanging listening on 14234

eventlet.spawn_n(later)
eventlet.sleep(1)
class Handle(BaseHTTPRequestHandler):
	def do_GET(self):
		print("get got")
		self.send_response(997,"boop")
import pdb
pdb.run('HTTPServer(("127.0.0.1",14234),Handle).serve_forever(None)')
