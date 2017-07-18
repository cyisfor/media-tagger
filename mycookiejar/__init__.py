import os,sys
oj = os.path.join

def setup(place,name="cookies.sqlite",policy=None):
	from . import db
	import sqlite3
	db.db = sqlite3.connect(oj(place,name))
	db.execute("PRAGMA journal_mode=WAL")
	from . import setup
	setup.policy = policy
	from . import jar
