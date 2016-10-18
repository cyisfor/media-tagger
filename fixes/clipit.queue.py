import os,struct,subprocess

pid = subprocess.Popen(["python3",os.path.expanduser("~/code/image/tagger/favorites/run.dbqueue.py")],
        stdin=subprocess.PIPE)

remote = pid.stdin

with open(os.path.expanduser("~/.local/share/clipit/history"),"rb") as inp:
	size = struct.unpack("i",inp.read(4))[0]
	print(size)
	assert(size == -1)
	inp.read(64)
	while True:
		size = inp.read(8)
		if not size: break
		size,data_type = struct.unpack("ii",size)
		data = inp.read(size)
		if data_type != 1: continue
		try: data = data.decode('utf-8')
		except UnicodeDecodeError: continue
		if 'http://' in data or 'https://' in data:
			print("got",data)
			remote.write(data+b'\n')


