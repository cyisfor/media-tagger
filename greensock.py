from greenlet import greenlet
import greenlet as g

SEND,RECV = range(2)

def tornadoOne(ret,sock,op,buf):
    if op == SEND:
        def respond(fd, events):
            nonlocal buf
            amt = sock.send(buf)
            if amt and amt < len(buf):
                buf = buf[amt:]
            else:
                ioloop.remove_handler(fd)
                ret.switch(amt)
        ioloop.add_handler(sock,respond,IOLoop.WRITE)
    elif op == RECV:
        def respond(fd, events):
            nonlocal buf
            amt = sock.recv_into(buf)
            ioloop.remove_handler(fd)
            ret.switch(amt)
        ioloop.add_handler(sock,respond,IOLoop.READ)

@greenlet
def tornado(*a):
    while True:
        tornadoOne(*a)
        a = greenlet.getcurrent().switch()
        
class zocket:
    def __init__(self,sock):
        self.sock = sock
    def send(self,buf):
        tornado.switch(greenlet.getcurrent(),self.sock,SEND,buf)
    def recv(self,buf):
        tornado.switch(greenlet.getcurrent(),self.sock,RECV,buf)

def test():
    a,b = socket.socketpair()
    a = zocket(a)
    b = zocket(b)
    buf = bytearray(0x1000)
    a.send("hi\n".encode())
    b.recv(buf)
    print(buf)
        
if __name__ == '__main__':
    test()
    
