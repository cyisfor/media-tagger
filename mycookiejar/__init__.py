import os,sys
oj = os.path.join

def setup(place,name="cookies.sqlite",policy=None):
	from . import db
	import sqlite3
	db.db = sqlite3.connect(oj(place,name))
	db.policy = policy
	from . import jar
	# let's not do this a second time, thx
	def pythonsucks(*a):
		raise RuntimeError("don't setup twice!")
	sys.modules[__name__] = pythonsucks
	return jar
