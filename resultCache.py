# SELECT id FROM etc -> CREATE TABLE resultCache... AS SELECT id FROM etc

import db

import hashlib,base64

db.setup("sql/resultCache.sql",source=True,named=False)

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

def fetch(name,offset,limit):
	db.retransaction()
	return db.execute('SELECT * FROM resultCache."q'+name+'" OFFSET $1 LIMIT $2',
										(offset,limit))

def expire():
	result = db.execute('SELECT resultCache.expireQueries()')[0][0]
	if result:
		print('expired',result,'queries')

def clear():
	while True:
		result = db.execute('SELECT resultCache.purgeQueries()')[0][0];
		if result:
			print('purged',result,'queries')
		if result < 1000: break
