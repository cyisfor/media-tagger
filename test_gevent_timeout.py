import gevent

@gevent.spawn
def longwaiter():
	gevent.sleep(3)
	print("we long waited!")

gevent.sleep(1)
print("short waited")
#longwaiter.kill()
gevent.wait([longwaiter])
