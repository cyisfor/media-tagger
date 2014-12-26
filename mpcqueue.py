# sigh... a glib IPC message sending queue

try:
    import pgi
    pgi.install_as_gi()
except ImportError: pass

from gi.repository import GLib

import json

import os

class Queue:
    source_id = None
    def send(self,message):
        message = json.dumps(message).encode('utf-8')+b'\1'
        self.channel.write_chars(message,len(message))
        print('wrote',message)
    def received(self,message): pass
    def __init__(self,channel):
        flags = channel.get_flags()
        channel.set_flags(flags|GLib.IO_FLAG_NONBLOCK)
        self.channel = channel
        if 0 != flags | GLib.IO_FLAG_IS_READABLE:
            self.buffer = b''
            self.source_id = channel.add_watch(GLib.IO_IN|GLib.IO_HUP, self.collect)
        self.flush = self.channel.flush
    def collect(self, io, condition):
        print(self,condition)
        if condition is GLib.IO_IN:
            self.buffer += io.read()
            messages = self.buffer.split(b'\1')
            self.buffer = messages[-1]
            for message in messages[:-1]:
                self.received(json.loads(message.decode('utf-8')))
            return True
        elif 0 != condition | GLib.IO_HUP:
            GLib.source_remove(self.source_id)
            del self.source_id
            if self.done: self.done()
        else:
            print('whu?')
        return True
    def finish(self, ondone):
        self.channel.flush()
        self.channel.add_watch(GLib.IO_OUT|GLib.IO_HUP, ondone)
    done = None

class Test(Queue):
    def __init__(self,channel,loop):
        super().__init__(channel)
        self.loop = loop
    def received(self, message):
        print('got message',message)
        if message == 42:
            self.done()
    def done(self):
        print('bye')
        self.loop.quit()

def test():
    r,w = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(w)
        loop = GLib.MainLoop()
        GLib.idle_add(lambda: Test(GLib.IOChannel.unix_new(r),loop) and False)
        loop.run()
        os._exit(0)
    os.close(r)
    queue = Queue(GLib.IOChannel.unix_new(w))
    loop = GLib.MainLoop()

    class Thingy:
        def done(self,*a):
            print('ayyy',a)
            loop.quit()
            print('yoy')
        def sendit(self):
            queue.send(3)
            queue.send(4)
            queue.send([5,6])
            queue.send(42)
            queue.finish(self.done)
    thingy = Thingy()
    GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, thingy.done)
    GLib.idle_add(thingy.sendit)
    loop.run()

if __name__ == '__main__':
    test()
