import db

def expire_queries():
	db.execute("SELECT resultcache.expirequeries()")

import threading
class Expirer(threading.Thread):
	def __init__(self):
		self.cond = threading.Condition()
	def run(self):
		import expire_queries
		while True:
			self.cond.wait()
			# expire 10 seconds after the first time we're poked
			# ignore intermediate pokes
			time.sleep(10)
			with self.cond:
				expire_queries()
	def poke(self):
		with self.cond:
			self.cond.notify_all()
	
if __name__ == '__main__':
	expire_queries()
else:
	import sys
	sys.modules[__name__] = Expirer()
	
