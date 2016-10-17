with open(os.path.expanduser("~/.local/share/clipit/history"),"rb") as inp:
	size = inp.read(1)
	print(size)
	assert(size == -1)
	inp.read(64)
	while True:
		size = inp.read(4)
		if not size: break
		size = struct.unpack("L",size)
		data_type = struct.unpack("L",inp.read(4))
		data = inp.read(size)
		print(size,data_type,data)
