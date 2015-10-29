from greenlet import greenlet
import greenlet as g

from tornado.ioloop import IOLoop

ioloop = IOLoop.instance()

SEND,RECV = range(2)


@greenlet
def tornadoOne():
    me = g.getcurrent()
    while True:
        ret,sock,op,buf = me.switch()
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

class zocket:
    def __init__(self,sock):
        self.sock = sock
    def send(self,buf):
        tornado.switch(greenlet.getcurrent(),self.sock,SEND,buf)
    def recv(self,buf):
        tornado.switch(greenlet.getcurrent(),self.sock,RECV,buf)

def test():
    def inloop():
        a,b = socket.socketpair()
        a = zocket(a)
        b = zocket(b)
        buf = bytearray(0x1000)
        a.send("hi\n".encode())
        b.recv(buf)
        print(buf)
        ioloop.stop()
    ioloop.add_callback(inloop)
    ioloop.start()
    
        
if __name__ == '__main__':
    test()
    
