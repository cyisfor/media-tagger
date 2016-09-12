# there is one reason, and one reason alone for writing an ORM
# to reduce copy and paste code repetition

# this is probably a horrible idea

from functools import wraps

def indent(text,what):
	return text.replace('\n','\n'+what)
import textwrap
level = 0
def uplevel(f):
	def wrap(*a,**kw):
		global level
		level += 1
		res = f(*a,**kw)
		lines = []
		for line in res.split('\n'):
			lines.extend(textwrap.wrap(line,width=120))
		ret = '\n  '.join(lines)
		level -= 1
		return ret
	return wrap

class SQL:
	def sql(self):
		raise NotImplementedError("This is some SQL statement.")
	def dump(self):
		return dump(self)

def dump(o):
	if isinstance(o,(tuple,list,set)):
		return [dump(oo) for oo in o]
	if hasattr(o,'__dict__'):
		return [o.__class__.__name__,dump(o.__dict__)]
	if isinstance(o,dict):
		d = dict()
		for n,v in o.items():
			v = dump(v)
			d[n] = v
		return d
	return o

def encode(o):
	if hasattr(o,'sql'):
		@uplevel
		def do():
			return o.sql()
		return do()
	elif o is None:
		return ''
	elif isinstance(o,(bytes,bytearray,memoryview)):
		return o.decode('utf-8')
	elif isinstance(o,str):
		return o
	else:
		try:
			s = None
			for oo in o:
				if s is None:
					s = encode(oo)
				else:
					s = s + ' ' + encode(oo)
			return s
		except TypeError:
			return str(o)

def complex(c):
	c.__complex = True
	return c

@complex
class With(SQL):
	def __init__(self, body, **clauses):
		self.body = body
		self.clauses = clauses
	def sql(self):
		clauses = []
		def add(d):
			for n,v in d.items():
				if n == 'clauses':
					add(v)
				else:
					args,body = v
					body = encode(body)
					if args:
						clauses.append(n+'('+encode(args)+') AS ('+body+ ')')
					else:
						clauses.append(n+' AS ('+body+ ')')
		add(self.clauses)
		return 'WITH\n'+',\n'.join(encode(clause) for clause in clauses) + '\n'+encode(self.body)

def create_table(name,*columns,temp=False,tail=None,idname='id'):
	s = 'CREATE '
	if temp:
		s += 'TEMPORARY '
	s += 'TABLE IF NOT EXISTS ' + encode(name) + '(\n'
	if idname:
		s += encode(idname)+" INTEGER PRIMARY KEY,\n "
		s += ',\n '.join(encode(column) for column in columns)
	s += ')\n'
	if tail is not None:
		s += tail
	return s

def column(name,type,*constraints,notNull=True):
	if type.startswith("REFERENCES"):
		constraints = (type,) + constraints
		type = "INTEGER"
	ret = encode((name, type))
	if constraints:
		ret += " " + encode(constraints)
	if notNull:
		ret += " NOT NULL"
	return ret

def references(table,*columns,cascade=True,default=None):
	s = 'REFERENCES '+encode(table)
	if not columns:
		s += '(id)'
	else:
		columns = (encode(column) for column in columns)
		s += '(' + ','.join(columns) + ')'
	if default is not None:
		s += ' DEFAULT '+encode(default)
	if cascade is True:
		s += ' ON DELETE CASCADE ON UPDATE CASCADE'
	elif cascade == 'restrict':
		s += ' ON DELETE RESTRICT ON UPDATE RESTRICT'
	return s

@complex
class Select(SQL):
	def __init__(self, what, From=None, where=None):
		self.what = what
		while isinstance(From,Group):
			From = From.clause
		self.From = From
		self.where = where
	def sql(self):
		if isinstance(self.what,(str)):
			args = self.what
		else:
			try: args = ', '.join(encode(arg) for arg in self.what)
			except TypeError:
				args = encode(self.what)
		s = 'SELECT '+args
		if self.From:
			s += '\nFROM '+encode(self.From)
			if self.where:
				s += '\nWHERE '+encode(self.where)
		return s

@complex
class Order(SQL):
	def __init__(self, clause, order):
		self.clause = clause
		self.order = order
	def sql(self):
		return encode(self.clause) + '\nORDER BY '+encode(self.order)

@complex
class Limit(SQL):
	def __init__(self, clause, offset=None, limit=None):
		self.clause = clause
		self.limit = limit
		self.offset = offset
	def sql(self):
		s = encode(self.clause)
		if self.offset:
			s += " OFFSET "+encode(self.offset)
		if self.limit:
			s += '\nLIMIT '+encode(self.limit)
		return s

class Group(SQL):
	def __init__(self, clause):
		self.clause = clause
	def sql(self):
		clause = self.clause
		while isinstance(clause,Group):
			clause = clause.clause
		return '(' + encode(self.clause) + ')'

@complex
class Unary(SQL):
	def __init__(self,clause):
		self.clause = clause
	def sql(self):
		return encode(self.clause)

class UnaryOperation(Unary):
	op = None
	def sql(self):
		op = self.op or self.__class__.__name__
		return encode(op) + ' ' + super().sql()

class BaseBinary(Unary):
	op = None
	def __init__(self, left, right):
		op = self.op or self.__class__.__name__
		super().__init__((left,op,right))

def asGroup(clause):
	if isinstance(clause,Group):
		return clause
	if isinstance(clause,(list,tuple,set)) or hasattr(clause,'__complex'):
		return Group(clause)
	return clause

class GroupBy(BaseBinary):
	op = 'GROUP BY'
	

@complex
class OnJoin(BaseBinary):
	def __init__(self, left, right, on):
		super().__init__(left,right)
		self.on = on
	def sql(self):
		return super().sql() + ' ON ' + encode(self.on)

class InnerJoin(OnJoin):
	op = 'INNER JOIN'

class OuterJoin(OnJoin):
	op = 'LEFT OUTER JOIN'

class FullJoin(BaseBinary):
	op = 'JOIN'

def grouping(c):
	oldinit = c.__init__
	@wraps(oldinit)
	def wrapinit(self,*a):
		return oldinit(self,*(asGroup(e) for e in a))
	c.__init__ = wrapinit
	return c

@grouping
class Binary(BaseBinary): pass
		
class AND(Binary): pass
class OR(Binary): pass
@grouping
class NOT(UnaryOperation):
	def __init__(self,clause):
		super().__init__(asGroup(clause))

class EQ(BaseBinary):
	op = '='
	def __init__(self,left,right):
		left = asGroup(left)
		if not isinstance(right,ANY):
			right = asGroup(right)
		super().__init__(left,right)
		
class IS(Binary): pass
class IN(Binary): pass

class Plus(Binary):
	op = '+'

class Intersects(Binary):
	op = '&&'

class Array(Unary):
	def sql(self):
		return 'ARRAY['+encode(self.clause)+']'
		
	
class Contains(Binary):
	op = '@>'
	def __init__(self,array,element):
		super().__init__(array,Array([element]))

@grouping
class AS(Binary): pass

@grouping
class EXISTS(Unary):
	def sql(self):
		return "EXISTS("+encode(self.clause)+")"

@grouping
class ANY(Unary):
	def __init__(self, clause):
		super().__init__(Group(clause))
	def sql(self):
		return ' ANY ' + super().sql()

@grouping
class EVERY(UnaryOperation): pass
	
class Func(SQL):
	def __init__(self, name, *args):
		self.name = name
		self.args = args
	def sql(self):
		return encode(self.name) + '(' + ', '.join(encode(arg) for arg in self.args) + ')';

class Union(SQL):
	def __init__(self, *selects):
		self.selects = selects
	def sql(self):
		return '\nUNION\n'.join(encode(s) for s in self.selects)

class Type(SQL):
	def __init__(self, clause, Type):
		self.clause = clause
		self.Type = Type
	def sql(self):
		return encode(self.clause) + '::' + encode(self.Type)

class array(Group):
	def sql(self):
		return 'array' + super().sql()
	
#################################################
def make_selins(db):
	def selins(name,*uniques):
		def provide_inserter(inserter=None):
			def get(self,*uniquevals):
				id = db.execute(
					"SELECT id FROM "+name+" WHERE "
					+ " AND ".join(val + " = ?" for val in uniques),
					uniquevals)
				if id:
					return id[0][0]
				if inserter:
					inserts = inserter().items()
					values = uniquevals + tuple(i[1] for i in inserts)
					keys = uniques + tuple(i[0] for i in inserts)
				else:
					# no extra columns to insert
					values = uniquevals
					keys = uniques
				db.execute("INSERT INTO "+name+" (" + ",".join(keys)
										 + ") VALUES (" + ",".join(("?",) * len(keys))
										 + ")",
										 values)
				return db.lastrowid
			return get
		return provide_inserter
	return selins

class argbuilder:
	n = 1
	def __init__(self):
		self.args = []
		self.names = {}
	def __call__(self,arg,name=None):
		if name is not None:
			if name in self.names:
				return self.names[name]
		num = '$'+str(self.n)
		self.n += 1
		if isinstance(arg,int):
			num = Type(num,'int')
		self.args.append(arg)
		if name is not None:
			self.names[name] = num
		return num
	
def main():
	from pprint import pprint
	stmt = Limit(
		Order(
			Select(
				["tableA.foo","tableD.bar","tableC.baz"],
				FullJoin(
					OuterJoin(
						InnerJoin("tableA","tableB","tableA.id = tableB.id"),
						"tableC",
						"tableA.id = tableC.id"),
					"tableD"),
				AND(EQ("tableB.beep","$1"),EQ("tableA.foo",Plus("tableC.baz",3)))),
			"tableB.bar, tableC.baz"),
		"$2",
		20)
	print(stmt.sql())
	print('---')
	herp =AND("3",EQ("A","B"))
	pprint(herp.dump())
	print(herp.sql())
	pprint(stmt.clause.clause.dump())
	print(stmt.clause.clause.sql())
	w = With(Select(['herp','derp'],
					InnerJoin('herp','derp',EQ('herp.herp','derp.derp')),
					IS(42,42)),
			 herp=('id',stmt.clause.clause),
			 derp=('a,b,c',herp))

	print(w.dump())
	print(w.sql())


if __name__ == '__main__':
	main()
