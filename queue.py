# sigh... a glib IPC message sending queue

import json

class Queue:
    source_id = None
    def send(self,message):
        self.channel.write_chars(json.dumps(message)+'\0')
    def received(self,message): pass
    def __init__(self,channel):
        self.source_id = channel.add_watch(GLib.IO_IN|GLib.IO_HUP, self.collect)
    def collect(self, io, condition):
        if condition is GLib.IO_IN|GLib.IO_HUP:
            GLib.source_remove(self.source_id)
            del self.source_id
        elif condition is GLib.IO_IN:
            self.buffer += io.read()
            messages = self.buffer.split('\0')
            self.buffer = messages[-1]
            for message in messages[:-1]:
                self.received(json.loads(message))
        else:
            print('whu?')

class Test(Queue):
    def received(self, message):
        print('got message',message)

def test():
    r,w = os.pipe()
    pid = os.fork()
    if pid == 0:
        queue = Test(GLib.IOChannel(r))
        GLib.MainLoop().run()
        os.exit(0)
    queue = Queue(GLib.IOChannel(w))
    queue.send(3)
    queue.send(4)
    queue.send({5,6})
    os.waitpid(pid)

test()
