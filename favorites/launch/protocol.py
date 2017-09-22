import note

from concurrent.futures import Future
from mygi import Gio,GLib

import struct

default_port = 4589

def lookup(addr):
	address = Future()
	def set_address(obj,result,resolver):
		addrs = resolver.lookup_by_name_finish(result)
		print("YAY",addrs[0])
		address.set_result(addrs[0])
	resolver = Gio.Resolver.get_default()
	resolver.lookup_by_name_async(addr, None, set_address, resolver)
	return address.add_done_callback

def to_catchup(info):
	inp = None
	out = None
	buf = bytearray(0x100)
	roff = 0
	woff = 0

	if not hasattr(info,'address'):
		info.address = '::1'
	if not hasattr(info,'port'):
		info.port = default_port

	client = Gio.SocketClient.new()
	have_address = lookup(info.address)
	have_connected = Future()

	ident = None

	def reconnect(conn):
		nonlocal have_connected
		have_connected = Future()
		def on_closed(obj, result, _):
			ok = conn.close_finish(result)
			if not ok:
				note.error("Bad close")
			connect()
		conn.close_async(0, None, on_closed, None)
		connect()
		
	def connect():
		@have_address
		def _(f):
			address = Gio.InetSocketAddress.new(f.result(),info.port)
			client.connect_async(address, None, on_connect, None)

	def readmoar(conn):
		if len(buf) - woff < 0x100:
			# this calls brk/mmap even less than C realloc...
			buf[len(buf):] = bytearray(0x100)
		inp.read_async(memoryview(buf)[woff:],0,None,on_input,conn)

	def on_input(obj, result, conn):
		nonlocal roff, woff, ident, buf
		amt = inp.read_finish(result)
		if amt < 0:
			reconnect(conn)
			return
		woff += amt
		head = memoryview(buf)[roff:woff]

		if ident is None:
			if len(head) < 4: return
			ident = struct.unpack("!I",head[:4])
			head = head[4:]
			info.starting(ident)

		# when sending progress, 2 bytes that is the floating point value where 0xFFFF = 100%
		# we can ignore all but the last complete progress
		# so 55 -> use 53,54, leave 55
		# 54 -> use 53, 54, leave none
		# etc
		hi = len(head) - len(head)%2
		lo = hi - 1
		if lo > 0:
			progress = struct.unpack("!H",head[lo:hi])
			if progress == 0xFFFF:
				ident = None
				info.done()
			else:
				info.progressed(progress / 0xFFFF)

		roff = hi+1
		if woff-roff > roff:
			# almost always true, except maybe if half a long path
			buf = bytearray(buf[roff:woff])
			woff -= roff
			roff = 0
		readmoar(conn)

	def on_connect(obj, result, user_data):
		nonlocal inp, out
		conn = client.connect_finish(result)
		inp = conn.get_input_stream()
		out = conn.get_output_stream()

		have_connected.set_result(conn)
		
		readmoar(conn)

	superpoke = None
	if hasattr(info,'poke'):
		superpoke = info.poke
		
	def poke():
		@have_connected.add_done_callback
		def _(f):
			conn = f.result()
			res = conn.get_output_stream().write(b"\0",None)
			if res != 0:
				reconnect(conn)
			if superpoke:
				superpoke()

	connect()
	info.poke = poke
	return info

def as_catchup(on_poked, port=default_port, address="::1"):
	service = Gio.SocketService.new()
	service.set_backlog(5)

	poking = None
	
	def un_poke():
		nonlocal poking
		on_poked()
		poking = None

	def on_input(obj, result, conn):
		nonlocal poking
		amt = inp.read_finish(result)
		# just ignore rapidfire pokes...
		# XXX: warn if amt == 0x10 for out of control client?
		if poking: return
		poking = Glib.timeout_add(500,un_poke)

	connections = []
		
	def on_accept(obj, result, user_data):
		conn, source = service.accept_finish(result)
		buf = bytearray(0x10)
		conn.get_input_stream().read_async(buf,0,None,on_input,conn)
		connections.append(conn)
	
	have_address = lookup(address)
	@have_address
	def _(f):
		address = Gio.InetSocketAddress.new(f.result(),port)
		service.add_address(address,
												Gio.SocketType.STREAM,
												Gio.SocketProtocol.DEFAULT,
												None)
		service.accept_async(None, on_accept, None)
		note("accepting")

	def on_name_written(obj, result, val):
		conn, out, name, on_ready = val
		ok, amt = val.write_finish(result)
		if not ok:
			conn.disconnect()
			conn = None
			Progress.start(name, on_ready)		
		
	class Progress:
		factor = 1
		def starting(self,ident,total):
			self.factor = 0xFFFF / total;
			conns = enumerate(connections)
			buf = struct.pack("!IH",ident,total)
			for i,conn in conns:
				out = conn.get_output_stream()
				ok, amt = out.write_all(buf,  None)
				if not ok:
					print("connection failed")
					conn.disconnect()
					del connections[i]
					# reset iterator
					conns = enumerate(connections)[i:]
		def progressed(self,progress):
			progress = round(progress * self.factor)
			progress = struct.pack("!H",progress)
			
			conns = enumerate(connections)
			for i,conn in conns:
				out = conn.get_output_stream()
				ok, amt = out.write_all(progress, None)
				if not ok:
					print("connection failed")
					conn.disconnect()
					del connections[i]
					# reset iterator
					conns = enumerate(connections)[i:]
	return Progress()
