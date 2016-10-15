def export(f): return f # meh

import sqlparse

import sys,os
sys.path.insert(0,os.path.expanduser("/home/code/postgresql-python"))
import postgresql as pg
from contextlib import contextmanager
from itertools import count, chain

ProgrammingError = pg.SQLError

tempctr = count(1)
place = os.path.dirname(__file__)
	
# @threadify
class DBProxy:
	ProgrammingError = pg.SQLError
	SQLError = pg.SQLError
	c = None
	def __init__(self):
		self.reopen()		
	@export
	def execute(self,*a,**kw):
		if not hasattr(self,'c'):
			self.reopen()
		return self.c.execute(*a,**kw)
	@export
	def retransaction(self,rollback=False):
		return pg.retransaction(self.c,rollback)
	@export
	def transaction(self):
		return pg.transaction(self.c)
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
		self.c.verbose = False
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
