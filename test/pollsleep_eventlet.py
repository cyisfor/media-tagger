import eventlet
import selectors as boop
from eventlet.green import socket, selectors
print(boop,selectors)

def connectandhang():
    c = socket.socket()
    ip = socket.gethostbyname("localhost")
    c.connect((ip, 14234))
		
    return c.recv(1024)

def later():
	eventlet.sleep(3)
	print("why is this never called?")

# make sure something hanging listening on 14234

eventlet.spawn(later)
connectandhang()
