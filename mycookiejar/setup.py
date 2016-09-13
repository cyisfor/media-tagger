import os,sys
oj = os.path.join

def setup(place,name="cookies.sqlite",policy=None):
	from mycookiejar import db
	import sqlite3
	db.db = sqlite3.connect(oj(place,name))
	import jar

import sys
sys.modules[__name__] = setup
