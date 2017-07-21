import eventlet
from eventlet.green.socketserver import TCPServer

def later():
	print("ummm")
	eventlet.sleep(3)
	print("why is this never called?")

# make sure something hanging listening on 14234

eventlet.spawn_n(later)
def handle(request,addr,thing):
	print("ok",request,addr,thing)
TCPServer(("127.0.0.1",14234),handle).serve_forever(None)
