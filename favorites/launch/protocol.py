# Gio suuuuuucks
# it randomly segfaults
# it raises errors with every read and write
# PLEASE let me use just python sockets

import socket,errno

import note

import threading
# Gtk p. much mandates this, since the GUI freezes
# DURING GLIB TIMEOUTS

from concurrent.futures import Future
from mygi import GLib

import struct

default_port = 4589

class Node:
	address = ('127.0.0.1', default_port)
	multicast = ('224.0.0.1', default_port + 1)

class Handler(Node):
	def starting(self,ident): pass
	def progressed(self,progress): pass
	def done(self): pass

def makesock():
	sock = socket.socket(family=socket.AF_INET,type=socket.SOCK_DGRAM,proto=socket.IPPROTO_UDP)
	return sock

def multicast(sock,group):
	mreq = struct.pack("4sl", socket.inet_aton(group[0]), socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

def send_all(out,buf,addr):
	done = Future()
	buf = memoryview(buf)
	def on_writeable(sock, condition, _, _2):
		nonlocal buf
		while buf:
			try:
				amt = out.sendto(buf,0,addr)
			except socket.error as e:
				if e.errno == EINTR:
					continue
				elif e.errno == errno.EAGAIN:
					return True # not false, still sending
				done.set_exception(e)
				note.error(e)
				return False
			assert amt >= 0
			buf = buf[amt:]
		# done sending
		done.set_result(True)
		return False
	if on_writeable(None,GLib.IO_OUT,None,None):
		GLib.unix_fd_add_full(0,
													out.fileno(),
													GLib.IO_OUT,
													on_writeable,
													None,None)
	return done

class Idler:
	"runs functions in the main thread"
	def __getattr__(self,name):
		func = getattr(self.o,name)
		if not callable(func):
			setattr(self,name,func)
			return func
		def wrapper(*a):
			GLib.idle_add(func,*a)
		setattr(self,name,wrapper)
		return wrapper
	def __init__(self,o):
		self.o = o

def to_catchup_start_reading(node):

	node = Idler(node)

	def reader():
		# note = Idler(note) eh, maybe...
		inp = makesock()
		inp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		res = inp.bind(node.multicast)
		multicast(inp,node.multicast)

		buf = bytearray(5)

		def ptype():
			# make sure we receive the full packet
			# (truncated and lost, if not)
			amt,addr = inp.recvfrom_into(buf,5)
			return buf[0]

		def readint(size):
			# had to recvfrom above
			if size == 4:
				fmt = '!I'
			elif size == 2:
				fmt = '!H'
			else:
				raise RuntimeError("foo")
			return struct.unpack(fmt,memoryview(buf)[1:1+size])[0]
		
		while True:
			pt = ptype()
			if pt == 0:
				ident = readint(4)
				node.starting(ident)
			elif pt == 1:
				progress = readint(2)
				note.yellow("progress",progress)
				node.progressed(progress / 0xFFFF)
				if progress == 0xFFFF:
					node.done()

	threading.Thread(target=reader,daemon=True,name="Reader").start()

def to_catchup(node=Handler):
	superpoke = None
	if hasattr(node,'poke'):
		superpoke = node.poke
			
	out = makesock()
	out.setblocking(False) # ? no real diff there...

	def poke():
			# 1 byte will either succeed or fail, no EAGAIN, or EINTR...
		try:
			res = out.sendto(b"\0",0,node.address)
		except socket.error as e:
			if e.errno == EAGAIN: return
			note("write error",e)
			return
		if superpoke:
			superpoke()

	node.poke = poke

	to_catchup_start_reading(node)

	return node # class decorator

trashbuf = bytearray(0x10)
	
def as_catchup(on_poked, node=Node):
	inp = makesock()
	out = makesock()
	out.setblocking(False)

	# catchup, input is unicast (just us) output is multicast
	# input is bound, output is the unbound
	# don't SUBSCRIBE to multicast on output
	# multicast(out,node.multicast)
	inp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	inp.bind(node.address)
	# ?
	out.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

	node.glibsucks = [inp,out]
	
	poking = None

	def un_poke():
		nonlocal poking
		on_poked()
		poking = None
		return False

	def reader():
		while True:
			try:
				amt,addr = inp.recvfrom_into(trashbuf)
			except socket.error as e:
				if e.errno == errno.EINTR: continue
				note.error(e)
				break
			note("poked from",amt,addr)

			nonlocal poking
			# just ignore rapidfire pokes...
			# XXX: warn if amt == 0x10 for out of control client?
			if poking:
				continue
			poking = GLib.timeout_add(500,un_poke)

	threading.Thread(target=reader,name="Pokey",daemon=1).start()

	class Progress:
		factor = 1
		def starting(self,ident,total):
			note("starting",ident)
			self.factor = 0xFFFF / total;
			ident = struct.pack("!BI",0,ident)
			note("ident",ident)
			
			return send_all(out,
											ident,
											node.multicast)

		def progressed(self,progress):
			#note("derp",progress*self.factor/0xFFFF)
			progress = round(progress * self.factor)
			progress = struct.pack("!BH",1,progress)

			return send_all(out,progress,node.multicast)
		def done(self):
			return send_all(out,struct.pack("!BH",1,0xFFFF),node.multicast)
	return Progress()
