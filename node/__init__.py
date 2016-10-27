if __name__ == '__main__':
	import syspath
import filedb
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

def connect_silly(name,backend_session,dofork=True):
	# since decorator returns the queue 
	# can just use the return value in your session handler
	import socket,select
	sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	addy = address(name)
	err = sock.connect_ex(addy)
	if err == 0:
		print("found existing backend node",name)
		return SocketQueue(sock)
	if dofork:
		is_ready,ready = os.pipe()
		pid = os.fork()
		assert pid >= 0
		if pid > 0:
			os.close(ready)
			select.select([is_ready],[],[])
			os.close(is_ready)
			print("ready!",addy)
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
		print("ready?")
		os.close(ready)
	while True:
		print("polling")
		for fd,event in poll.poll():
			print("got event",fd,event)
			if fd == sockno:
				sess,addr = sock.accept()
				print("got connect from",addr)
				queue = SocketQueue(sess)
				try:
					# to allow initialization in the backend process:
					queue.session = backend_session(queue)
				except BrokenPipeError: continue
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
				print("Strange fd?",fd);

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
			self.buf.extend(0 for a in range(0x1000)) # meh python sucks
		view = memoryview(self.buf)[self.writepoint:]
		nbytes = self.sock.recv_into(view)
		if not nbytes: return
		self.writepoint += nbytes
		self.parse_some()
	def send(self,message):
		assert len(message) != 0
		assert self.sock.send(struct.pack("H",len(message)) + message) == 2 + len(message)
	length = None
	def parse_some(self):
		def readlen():
			import note
			self.length = struct.unpack("H",self.buf[:2])[0]
			assert self.length > 0, self.buf
			note("message length",self.length)
			self.buf = self.buf[2:]
			self.writepoint -= 2
		if self.length is None:
			if self.writepoint < 2: return
			readlen()
		while True:
			if self.writepoint < self.length: return
			message = memoryview(self.buf)[:self.length]
			self.session(message)
			self.buf = self.buf[:self.length]
			self.writepoint -= self.length
			if self.writepoint < 2:
				self.length = None
				return
			readlen()

def example():
	@connect("test")
	def queue(queue):
		count = 0
		def session(message):
			nonlocal count
			message = bytes(message).decode()
			print("got message",message)
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
