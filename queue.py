# sigh... a glib IPC message sending queue

from gi.repository import GLib

import json

import os

class Queue:
    source_id = None
    def send(self,message):
        message = json.dumps(message).encode('utf-8')+b'\1'
        self.channel.write_chars(message,len(message))
    def received(self,message): pass
    def __init__(self,channel):
        channel.set_flags(channel.get_flags()|GLib.IO_FLAG_NONBLOCK)
        self.channel = channel
        self.source_id = channel.add_watch(GLib.IO_IN|GLib.IO_HUP, self.collect)
        self.flush = self.channel.flush
        self.buffer = b''
    def collect(self, io, condition):
        if condition is GLib.IO_IN:
            self.buffer += io.read()
            messages = self.buffer.split(b'\1')
            self.buffer = messages[-1]
            for message in messages[:-1]:
                self.received(json.loads(message.decode('utf-8')))
        elif 0 != condition | GLib.IO_HUP:
            GLib.source_remove(self.source_id)
            del self.source_id
        else:
            print('whu?')

class Test(Queue):
    def __init__(self,channel,loop):
        super().__init__(channel)
        self.loop = loop
    def received(self, message):
        print('got message',message)
        if message == 42:
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
        os.exit(0)
    os.close(r)
    queue = Queue(GLib.IOChannel.unix_new(w))
    def done():
        os.close(w)
        loop.quit()
        print('yoy')
    def sendit():
        queue.send(3)
        queue.send(4)
        queue.send([5,6])
        queue.send(42)
        queue.flush()
        GLib.idle_add(done)
    GLib.idle_add(sendit)
    loop = GLib.MainLoop()
    loop.run()
    os.waitpid(pid,0)

test()
