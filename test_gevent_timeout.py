import gevent

longwait = gevent.timeout.Timeout(100)
shortwait = gevent.timeout.Timeout(1)

@gevent.spawn
def longwaiter():
	with longwait:
		print("we waited!")
	print("long done")


with shortwait:
	print("short waited")
longwait.cancel()
	
