import threading,queue
class Queue(queue.Queue):
	def __call__(self,f):
		self.put(f)
		return 
		
def makeWorkers(foreground,*inits):
	initsem = threading.Semaphore(0)
	def drain_foreground(g):
		for q in g:
			if q is foreground: continue
			q.put(g)
			# we have to trust q to return to us at some point...
			break
	def in_foreground(f):
		def wrapper(*a,**kw):
			g = f(*a,**kw)
			drain_foreground(g)
		return wrapper
	class Thread(threading.Thread):
		def __init__(self, init, q):
			super().__init__(daemon=True)
			self.init = init
			self.q = q
		def run(self):
			print('background worker going')
			self.init()
			initsem.release()
			def drain_task(gen):
				if gen is foreground:
					# HAX
					# foreground is like Glib.idle_add
					# so resumes our generator in the foreground
					foreground(lambda: drain_foreground(gen))
					return
				try:
					for q in gen:
						if q is foreground:
							# sigh
							foreground(lambda: drain_foreground(gen))
							return
						if q is not self.q:
							# switch to a different thread...
							q.put(gen)
							return
						# or continue to drain this generator ourself
				except TypeError:
					# must have put a lambda into our queue
					return gen()
					
				print("something finished. exit here?")
			while True:
				try:
					note.yellow("uhhhhhhh")
					gen = self.q.get()
					while gen:
						gen = drain_task(gen)
				except queue.Empty:
					# huh? but blocking?
					time.sleep(1)
				finally:
					self.q.task_done()
	qs = tuple(Queue() for _ in range(len(inits)))
	print('boop?',len(inits))
	for i,init in enumerate(inits):
		Thread(init,qs[i]).start()
	for i in range(len(inits)):
		initsem.acquire()
	return (in_foreground,)+qs
