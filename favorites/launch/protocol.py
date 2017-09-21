from myfuture import Future

default_port = 4587

def lookup(addr):
	address = Future()
	def set_address(addrs):
		address.set_result(addrs[0])
	Gio.Resolver().lookup_by_name_async(addr,callback=set_address)
	return address.add_done_callback

def to_catchup(on_progress,port=default_port,address="::1"):
	inp = None
	out = None
	buf = bytearray(0x100)
	roff = 0
	woff = 0

	client = Gio.SocketClient.new()
	have_address = lookup(address)
	have_connected = Future()

	curname = None

	def reconnect():
		nonlocal have_connected
		have_connected = Future()
		client.disconnect()
		connect()
		
	def connect():
		@have_address
		def _(address):
			address = Gio.InetSocketAddress.new(address,port)
			client.connect_async(address, None, on_connect, None)

	def readmoar():
		if len(buf) - woff < 0x100:
			# this calls brk/mmap even less than C realloc...
			buf[len(buf):] = bytearray(0x100)
		inp.read_async(memoryview(buf)[woff:],0,None,on_input,conn)

	def on_input(obj, result, conn):
		nonlocal roff, woff, progress, curname
		amt = inp.read_finish(result)
		if amt < 0:
			reconnect()
			return
		woff += amt
		head = memoryview(buf)[roff:woff]

		if curname is None:
			nl = head.find(b'\n')
			if nl != -1:
				curname = head[:nl].decode('utf-8')
				head = head[nl+1:]

		# when sending progress, 2 bytes that is the floating point value where 0xFFFF = 100%
		# we can ignore all but the last complete progress
		# so 55 -> use 53,54, leave 55
		# 54 -> use 53, 54, leave none
		# etc
		hi = len(head) - len(head)%2
		lo = hi - 1
		if lo > 0:
			progress = struct.unpack("!H",head[lo:hi])
			on_progress(progress / 0xFFFF)
			if progress == 0xFFFF:
				curname = None
		roff = hi+1
		if woff-roff > roff:
			# almost always true, except maybe if half a long path
			buf = bytearray(buf[roff:woff])
			woff -= roff
			roff = 0
		readmoar()

	def on_connect(obj, result, user_data):
		nonlocal inp, out
    conn = client.connect_finish(result)
    inp = conn.get_input_stream()
		out = conn.get_output_stream()

		have_connected.set_result([inp,out])
		
		readmoar()

	def poke():
		@have_connected.add_done_callback
		def _(val):
			inp,out = val
			res = out.write(b"\0",None)
			if res != 0:
				reconnect()

	connect()
	return poke

def as_catchup(on_poked, port=default_port):
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
		conn.read_async(buf,0,None,on_input,conn)
		connections.append(conn)
	
	have_address = lookup(address)
	@have_address
	def _(address):
		address = Gio.InetSocketAddress.new(address,port)
		service.add_address(address)
		service.accept_async(None, on_accept, None)

	def on_name_written(obj, result, val):
		conn, out, name, on_ready = val
		ok, amt = val.write_finish(result)
		if not ok:
			conn.disconnect()
			conn = None
			Progress.start(name, on_ready)		
		
	class Progress:
		factor = 1
		def __init__(self,name,total):
			self.name = name
			self.factor = 0xFFFF / total;
			conns = enumerate(connections)
			for i,conn in conns:
				out = conn.get_output_stream()
				buf = name.encode("utf-8") + "\n" + struct.pack("!H",total)
				ok, amt = out.write_all(buf,  None)
				if not ok:
					print("connection failed")
					conn.disconnect()
					del connections[i]
					# reset iterator
					conns = enumerate(connections)[i:]
		def progress(self,progress):
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
	return Progress
