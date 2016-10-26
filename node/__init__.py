import filedb
import os

# new strategy, named nodes like "catchup" etc that each have a named socket
# to use, try to connect to the socket, if fail, launch process then retry

def address(name):
	return os.path.join(filedb.temp,"socket-"+name)

def connect(name,frontend_session,backend_session):
	import socket
	sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	addy = address(name)
	err = sock.connect_ex(addy)
	if err == 0: return sock
	is_ready,ready = os.pipe()
	pid = os.fork()
	assert pid >= 0
	if pid == 0:
		select.select([is_ready])
		os.close(is_ready)
		sock.connect(addy)
		return SocketQueue(sock,frontend_session)
	sock.bind(addy)
	sock.listen(5)
	poll = select.poll()
	sockno = sock.fileno()
	poll.register(sockno,select.POLLIN)
	sessions = dict()
	while True:
		for fd,event in poll.poll():
			if fd == sockno:
				sess = sock.accept()
				sessno = sess.fileno()
				poll.register(sessno, select.POLLIN)
				queue = SocketQueue(sess, make_session())
				sessions[sessno] = queue
			elif fd in sessions:
				queue = sessions[fd]
				queue.read_more()
			else:
				print("Strange fd?",fd);


class SocketQueue:
	def __init__(self, sock, make_session):
		self.session = make_session(self)
		self.sock = sock
		self.buf = bytearray()
		self.writepoint = 0
	def read_some(self):
		if len(self.buf) - self.writepoint < 0x1000:
			self.buf.extend(0 for 0 in range(0x1000)) # meh python sucks
		view = memoryview(self.buf)[self.writepoint:]
		nbytes = self.sock.recv_into(view)
		if not nbytes: return
		self.writepoint += nbytes
		self.parse_some()
	def send(self,message):
		self.sock.write(struct.pack("H",len(message)))
		self.sock.write(message)
	def parse_some(self):
		def readlen():
			self.length = struct.unpack("H",self.buf[:2])
			self.buf = self.buf[2:]
			self.writepoint -= 2
		if self.length is None:
			if self.writepoint < 2: return
			readlen()
		while True:
			if self.writepoint < self.length: return
			message = memoryview(self.buf)[:self.length]
			session(message)
			self.buf = self.buf[:self.length]
			self.writepoint -= self.length
			if self.writepoint < 2:
				self.length = None
				return
			readlen()

def test():
	def backend_session(queue):
		count = 0
		def session(message):
			nonlocal count
			print("got message",message)
			count += int(message)
			queue.send(str(count).encode())
		return session
	def frontend_session(queue):
		derp = 10
		queue.send(str(derp).encode())
		def session(message):
			nonlocal derp
			if derp <= 0: raise SystemExit
			derp -= 1
			print("got count",int(message))
			queue.send(str(derp).encode())
	connect("test",frontend_session, backend_session)
			
if __name__ == '__main__':
	test()
