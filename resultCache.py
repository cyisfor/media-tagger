# SELECT id FROM etc -> CREATE TABLE resultCache... AS SELECT id FROM etc

import db

#db.execute("DROP SCHEMA resultCache CASCADE")

import hashlib,base64

def schema(f):
	def wrapper(*a,**kw):
		try:
			return f(*a,**kw)
		except db.Error as e:
			if not b'schema "resultcache" does not exist' in e['message']:
				raise
			
			intrans = db.c.inTransaction
			if intrans:
				db.rollback()
			print("loading schema...")
			db.setup("sql/resultCache.sql",source=True,named=False)
			if intrans:
				db.begin()
		# now try it with the db setup
		return f(*a,**kw)
	return wrapper

@schema
def get(query,args,docache=True):
	#db.c.verbose = True
	if hasattr(args,'values'):
		vals = sorted(n+str(v) for n,v in args.items())
	else:
		args = list(args)
		vals = args
	name = hashlib.sha1((query +
											 ''.join(str(arg) for arg in vals)).encode('utf-8'))
	name = base64.b64encode(name.digest(),altchars=b'-_').decode().replace('=','')
	if docache == False:
		return name
	print(query)
	print("caching",args)
	with db.transaction():		
		exists = db.execute("SELECT resultCache.cleanQuery($1)",(name,))[0][0]

		if exists:
			print("already cached")
		else:
			try: 
				db.execute('CREATE TABLE resultCache."q'+name+'" AS '+query,args)
			except db.ProgrammingError as e:
				if not 'already exists' in e.info['message'].decode('utf-8'): raise
		db.execute('SELECT resultCache.updateQuery($1)',(name,))
		return name;

@schema
def fetch(name,offset,limit):
	db.retransaction()
	return db.execute('SELECT * FROM resultCache."q'+name+'" OFFSET $1 LIMIT $2',
										(offset,limit))

@schema
def expire():
	result = db.execute('SELECT resultCache.expireQueries()')[0][0]
	if result:
		print('expired',result,'queries')

@schema
def clear():
	while True:
		result = db.execute('SELECT resultCache.purgeQueries()')[0][0];
		if result:
			print('purged',result,'queries')
		if result < 1000: break

if __name__ == '__main__':
  clear()
