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
        if flags & GLib.IO_FLAG_IS_READABLE:
            print('reading channel',flags | GLib.IO_FLAG_IS_READABLE,flags)
            self.buffer = b''
            self.source_id = channel.add_watch(GLib.IO_IN|GLib.IO_HUP, self.collect,self)
        else:
            print("writing channel",flags)
        self.flush = self.channel.flush
    def collect(self, io, condition, udata):
        print('collectingUGH')
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
        sys.stdout.flush()
        if message == 42:
            self.done()
    def done(self):
        print('bye')
        self.loop.quit()

def test():
    pipe = '/tmp/derp.pipe'
    try: os.mkfifo(pipe)
    except OSError: pass
    
    if 'read' in os.environ:
        r = os.open(pipe,os.O_RDONLY)
        loop = GLib.MainLoop()
        t = Test(GLib.IOChannel.unix_new(r),loop)
        t.channel.ref()
        print('test?',t.channel)
        GLib.timeout_add(2,(lambda *a: print('idled',a) and False))
        loop.run()
        print('oy')
        os._exit(0)
    print('writing')
    w = os.open(pipe,os.O_WRONLY)
    queue = Queue(GLib.IOChannel.unix_new(w))
    loop = GLib.MainLoop()

    class Thingy:
        def done(self,*a):
            print('ayyy',a)
            #loop.quit()
            print('yoy')
        def sendit(self,wha):
            print(wha)
            queue.send(3)
            queue.send(4)
            queue.send([5,6])
            queue.send(42)
            queue.finish(self.sent)
            return False
        def sent(self,*a):
            print('sent',a)
    thingy = Thingy()
    #GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, thingy.done)
    GLib.timeout_add(1000,thingy.sendit)
    loop.run()
    print(thingy)

if __name__ == '__main__':
    test()
