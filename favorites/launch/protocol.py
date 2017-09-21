def do_catchup():
	inp = None
	out = None
	buf = bytearray(0x100)
	roff = 0
	woff = 0

	def readmoar():
		if len(buf) - woff < 0x100:
			# realloc?
			buf[-1:] = bytearray(0x100)
			
			
		inp.read_async(memoryview(buf)[woff:])		
	
	def on_input(obj, result, conn):
		amt = inp.read_finish(result)
		if amt < 0:
			reconnect()
			return
		
	def on_connect(obj, result, user_data):
		nonlocal inp, out
    conn = client.connect_finish(result)
    inp = conn.get_input_stream()
		out = conn.get_output_stream()

		readmoar()

