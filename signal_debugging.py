import signal,os
def start_debugging(signal, frame):
	import pdb
	pdb.Pdb().set_trace(frame)
try:
	signal.signal(signal.SIGUSR1,start_debugging)
	print("debugging on kill -USR1",os.getpid())
except ValueError: pass
