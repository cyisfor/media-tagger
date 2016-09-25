import db

def expire_queries():
	db.execute("SELECT resultcache.expirequeries()")

import threading
class Expirer(threading.Thread):
	def __init__(self):
		super().__init__(daemon=True)
		self.cond = threading.Condition()
	def run(self):
		import note
		import time
		while True:
			with self.cond:
				self.cond.wait()
			# expire 10 seconds after the first time we're poked
			# ignore intermediate pokes
			time.sleep(10)
			with self.cond:
				note.red("expiring queries")
				expire_queries()
	def poke(self):
		with self.cond:
			self.cond.notify_all()
	
if __name__ == '__main__':
	expire_queries()
else:
	import sys
	def startup():
		e = Expirer()
		e.start()
		return e.poke
	sys.modules[__name__] = startup

	
