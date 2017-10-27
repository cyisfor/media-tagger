import sqlparse

import sys,os
sys.path.insert(0,os.path.expanduser("/home/code/postgresql-python"))
import postgresql as pg
from contextlib import contextmanager
from itertools import count, chain

ProgrammingError = pg.SQLError
Error = pg.SQLError

import gevent
import gevent.queue

queue = gevent.queue.Queue()
def export(f):
	return f
	# since the database cannot execute while executing (asynchronously)
	# need to queue up requests to do stuff, switch back when done
	def wrapper(*a,**kw):
		if gevent.getcurrent() == drainQueue:
			print("calling queue in queue...")
			return f(*a,**kw)
		resume = gevent.event.AsyncResult()
		queue.put((f,a,kw,resume))
		return resume.get()
	return wrapper

@gevent.spawn
def drainQueue():
	while True:
		f,a,kw,resume = queue.get()
		try:
			print("run",f)
			ret = f(*a,**kw)
			print("runnnn",ret)
			resume.set(ret)
		except Exception as e:
			print("boooo")
			import traceback
			traceback.print_exc()
			resume.set_exception(e)

tempctr = count(1)
place = os.path.dirname(__file__)
	
# @threadify
class DBProxy:
	ProgrammingError = pg.SQLError
	Error = Error
	SQLError = pg.SQLError
	c = None
	def __init__(self):
		self.reopen()
	@export
	def copy(self,*a,**kw):
		return self.c.copy(*a,**kw)
	@export
	def execute(self,*a,**kw):
		if not hasattr(self,'c'):
			self.reopen()
		return self.c.execute(*a,**kw)
	@export
	def retransaction(self,rollback=False):
		return pg.retransaction(self.c,rollback)
	@export
	def cursor(self,name,stmt,args=()):
		return self.c.cursor(name,stmt,args)
	@export
	def transaction(self):
		return pg.transaction(self.c)
	@export
	def saved(self):
		return pg.saved(self.c)
	@export
	def registerDecoder(self,decoder,name,namespace='public'):
		if not self.c: self.reopen()
		return self.c.registerDecoder(decoder,name,namespace)
	@export
	@contextmanager
	def temporaryTable(self, columns,notSoTemp=False):
		name = "temptable{}".format(tempctr.__next__())
		if notSoTemp:
			prefix = "CREATE"
		else:
			prefix = "CREATE TEMPORARY"
		try:
			execute(prefix+" TABLE "+name+" ("+columns+")")
			yield name
		finally:
			execute("DROP TABLE "+name)

	@export
	def reopen(self):
		try:
			with open("passwd") as inp:
				password = inp.read()
		except IOError:
			password = None
		self.c = pg.Connection(dbname='pics',port=5433,host="/home/run",password=password)
		#self.c.verbose = True
		#self.c.out = open('/tmp/self.log','at')
		password = None

	@export
	def vsetup(self, *stmts):
		for stmt in stmts:
			self.execute(stmt)

	@export
	def setup(self, *stmts, **kw):
		if kw.get('source'):
			stmts = chain.from_iterable((self.source(stmt,kw.get('named',True)) for stmt in stmts))
		#execute("COMMIT")
		for stmt in stmts:
			try:
				self.execute(stmt)
			except ProgrammingError as e:
				if self.c.verbose:
					sys.stdout.write(stmt)
					print('')
					sys.stdout.write(e.info['message'].decode('utf-8'))
					print('')
	
	# either returns {name=statement...} or [statement...] depending on file format...
	@export
	def source(self, path,namedStatements=True):
		arg = open(os.path.join(place,path))
		with arg as inp:

			if namedStatements:
				return dict(sqlparse.parse(inp))
			stmts = []
			value = []
			inQuote = False
	
			# this should roughly parse postgresql dumps
			for line in inp:
				if line.lstrip().startswith('--'): continue
				line = line.rstrip()
				if not line: continue
				if '$$' in line: 
					inQuote = not inQuote
				ended = not inQuote and line[-1]==';'
				if ended:
					line = line[:-1]
				value.append(line)
				if ended:
					stmts.append("\n".join(value))
					value[:] = ()
		return stmts
	def tableExists(self,table,schema='public'):
		stmt = '''
SELECT EXISTS (
	SELECT 1 
	FROM   pg_catalog.pg_class c
	JOIN   pg_catalog.pg_namespace n ON n.oid = c.relnamespace
	WHERE  n.nspname = $1
	AND	c.relname = $2
--	AND	c.relkind = 'r'	-- only tables(?)
);
'''
		return self.execute(stmt,(schema,table))[0][0]

sys.modules[__name__] = DBProxy()

