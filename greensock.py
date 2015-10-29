from greenlet import greenlet
import greenlet as g

from tornado.ioloop import IOLoop

import socket

ioloop = IOLoop.instance()

SEND,RECV = range(2)


@greenlet
def tornado(ret):
    # uhhh then ret.switch(something) on callback and start ioloop?
    def repeat(ret,sock,op,buf):
        if op == SEND:
            def respond(fd, events):
                nonlocal buf
                amt = sock.send(buf)
                if amt and amt < len(buf):
                    buf = buf[amt:]
                else:
                    ioloop.remove_handler(fd)
                    repeat(*ret.switch(amt))
            ioloop.add_handler(sock,respond,IOLoop.WRITE)
        elif op == RECV:
            def respond(fd, events):
                nonlocal buf
                amt = sock.recv_into(buf)
                ioloop.remove_handler(fd)
                repeat(*ret.switch(amt))
            ioloop.add_handler(sock,respond,IOLoop.READ)
    repeat(*a)
    
class zocket:
    def __init__(self,sock):
        self.sock = sock
    def send(self,buf):
        return tornado.switch(greenlet.getcurrent(),self.sock,SEND,buf)
    def recv(self,buf):
        return tornado.switch(greenlet.getcurrent(),self.sock,RECV,buf)

def test():
    def inloop():
        a,b = socket.socketpair()
        a = zocket(a)
        b = zocket(b)
        buf = bytearray(0x1000)
        a.send("hi\n".encode())
        print(b.recv(buf))
        print(buf[:3])
        ioloop.stop()
    ioloop.add_callback(inloop)
    ioloop.start()
    
        
if __name__ == '__main__':
    test()
    
