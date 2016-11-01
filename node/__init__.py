if __name__ == '__main__':
	import syspath
import filedb
import note

import os
import struct

# new strategy, named nodes like "catchup" etc that each have a named socket
# to use, try to connect to the socket, if fail, launch process then retry

def address(name):
	return os.path.join(filedb.temp,"socket-"+name)

def connect(name):
	def connect_back(backend_session):
		return connect_silly(name,backend_session)
	return connect_back

class SocketQueue:
	def __init__(self, sock):
		self.sock = sock
		self.buf = bytearray()
		self.writepoint = 0
	def read_all(self,session=None):
		if session:
			self.session = session
		while True:
			self.read_some()
	def read_some(self):
		if len(self.buf) - self.writepoint < 0x1000:
			self.buf.extend(b'Q'[0] for a in range(0x1000)) # meh python sucks
		view = memoryview(self.buf)[self.writepoint:]
		nbytes = self.sock.recv_into(view)
		if not nbytes: return
		self.writepoint += nbytes
		self.parse_some()
	def send(self,message):
		assert len(message) != 0
		blob = struct.pack("H",len(message)) + message
		assert self.sock.send(blob) == 2 + len(message)
	length = None
	def parse_some(self):
		def readlen():
			import note
			self.length = struct.unpack("H",self.buf[:2])[0]
			assert self.length > 0, self.buf
			self.buf = self.buf[2:]
			self.writepoint -= 2
		if self.length is None:
			if self.writepoint < 2: return
			readlen()
		while True:
			if self.writepoint < self.length: return
			message = memoryview(self.buf)[:self.length]
			self.session(message)
			self.buf = self.buf[self.length:]
			self.writepoint -= self.length
			if self.writepoint < 2:
				self.length = None
				return
			readlen()

def reconnecting(mem):
	def wrapper(self,*a,**kw):
		while True:
			try:
				return mem(self,*a,**kw)
			except (BrokenPipeError,ConnectionResetError):
				print("lost connection... reconnecting")
				time.sleep(1)
				self.reconnect()
			
class connect_silly(SocketQueue):
	@reconnecting
	def send(self,message):
		super().send(message)
	def __init__(self,name,backend_session,dofork=True):
		super().__init__(None)
		self.name = name
		self.backend_session = backend_session
		self.dofork = dofork
		self.reconnect()
	def reconnect(self):
		import socket
		self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		addy = address(name)
		err = sock.connect_ex(addy)
		if err == 0:
			note.blue("found existing backend node",name)
			return
		if self.dofork:
			is_ready,ready = os.pipe()
			pid = os.fork()
			assert pid >= 0
			if pid > 0:
				os.close(ready)
				select.select([is_ready],[],[])
				os.close(is_ready)
				note("ready!",addy)
				sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
				sock.connect(addy)
				return SocketQueue(sock)
			os.close(is_ready)
		try: os.unlink(addy)
		except OSError: pass
		sock.bind(addy)
		sock.listen(5)
		poll = select.poll()
		sockno = sock.fileno()
		poll.register(sockno,select.POLLIN)
		sessions = dict()
		if dofork:
			note.yellow("ready?")
			os.close(ready)
		while True:
			note.blue("polling")
			for fd,event in poll.poll():
				if fd == sockno:
					sess,addr = sock.accept()
					note("got connect from",addr)
					queue = SocketQueue(sess)
					try:
						# to allow initialization in the backend process:
						queue.session = self.backend_session(queue)
					except BrokenPipeError:
						continue
					sessno = sess.fileno()
					poll.register(sessno, select.POLLIN)
					sessions[sessno] = queue
				elif fd in sessions:
					if event & select.POLLHUP:
						poll.unregister(fd)
						os.close(fd)
						continue
					queue = sessions[fd]
					try:
						queue.read_some()
					except BrokenPipeError:
						poll.unregister(fd)
						os.close(fd)
						continue
				else:
					note.alarm("Strange fd?",fd);



def example():
	@connect("test")
	def queue(queue):
		count = 0
		def session(message):
			nonlocal count
			message = bytes(message).decode()
			note.yellow("got message",message)
			count += int(message)
			queue.send(str(count).encode())
		return session
	derp = 10
	queue.send(str(derp).encode())
	@queue.read_all
	def _(message):
		nonlocal derp
		if derp <= 0:
			print("all done")
			raise SystemExit
		derp -= 1
		print("got count",int(message))
		queue.send(str(derp).encode())

if __name__ == '__main__':
	example()
