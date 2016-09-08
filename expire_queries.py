import db

def expire_queries():
	db.execute("SELECT resultcache.expirequeries()")

if __name__ == '__main__':
	expire_queries()
else:
	import sys
	sys.modules[__name__] = expire_queries
