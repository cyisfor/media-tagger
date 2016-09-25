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
	class Thread(threading.Thread):
		def __init__(self, init, q):
			super().__init__(daemon=True)
			print('boop',init)
			self.init = init
			self.q = q
		def run(self):
			print('background worker going')
			self.init()
			initsem.release()
			while True:
				try: gen = self.q.get()
				except queue.Empty:
					# huh? but blocking?
					time.sleep(1)
					continue
				try:
					print('dequeue',gen)
					for q in gen:
						if q is foreground:
							# HAX
							# foreground is like Glib.idle_add
							# so resumes our generator in the foreground
							foreground(lambda: drain_foreground(gen))
							break
						elif q is not self.q:
							break
						# else stay in this thread b/c yielded our own queue
					else:
						print("something finished. exit here?")
						continue
					# gen yielded q, (not us) so it wants in this queue
					q.put(gen)
				finally:
					self.q.task_done()
	qs = tuple(Queue() for _ in range(len(inits)))
	print('boop?',len(inits))
	for i,init in enumerate(inits):
		Thread(init,qs[i]).start()
	for i in range(len(inits)):
		initsem.acquire()
	return (in_foreground,)+qs
