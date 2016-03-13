import myserver
import note
note.monitor(myserver)
from tracker_coroutine import coroutine
from tornado.concurrent import Future
from tornado.ioloop import IOLoop

import time,sys

class Handler(myserver.ResponseHandler):
    def received_header(self,name,value):
        print('got header yay',name,value)
        return super().received_header(name,value)
    def data_received(self,data):
        print('== received')
        print('='*60)
        sys.stdout.flush()
        sys.stdout.buffer.write(data)
        print('='*60)
    @coroutine
    def get(self):
        yield self.write("before headers\n")
        yield self.send_status(200,"Okie")
        yield self.send_header("Content-Type","text/plain; charset=utf-8")
        yield self.write("after header\n")
        future = Future()
        @coroutine
        def send_time(level):
            try:
                yield self.send_header("X-Time",str(time.time()))
            except Exception as e:
                future.set_exception(e)
            else:
                if level > 0:
                    self.stream.io_loop.call_later(0.5,send_time,level-1)
                else:
                    future.set_result(True)
        yield send_time(2)
        yield future
        yield self.write("end of headers\n")
        yield self.end_headers()

myserver.Server(Handler).listen(8934)

IOLoop.instance().start()
