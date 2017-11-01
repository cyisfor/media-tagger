# SELECT id FROM -> CREATE TABLE FROM SELECT etc

import db

import hashlib,base64
print("BAR")
db.setup("sql/resultCache.sql",source=True,named=False)
print("BAR")

def get(query,args,docache=True):
	#db.c.verbose = True
	with db.transaction():
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
		try: 
			db.execute('CREATE TABLE resultCache."q'+name+'" AS '+query,args)
			#raise SystemExit
			db.execute('SELECT resultCache.updateQuery($1)',(name,))
		except db.ProgrammingError as e:
			if not 'already exists' in e.info['message'].decode('utf-8'): raise
		return name;

def query(name,offset,limit):
	db.retransaction()
	return db.execute('SELECT * FROM resultCache."q'+name+'" OFFSET $1 LIMIT $2',
										(offset,limit))

def clear():
	while True:
		result = db.execute('SELECT resultCache.expireQueries()')[0][0];
		if result:
			print('cleared',result,'results')
		if result < 1000: break
