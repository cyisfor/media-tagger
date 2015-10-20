# this is probably a horrible idea

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
        return o.sql()
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

class Complex(SQL): pass

class With(Complex):
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
                    body = encode(body).replace('\n','\n\t')
                    clauses.append(n+'('+encode(args)+') AS ('+body+ ')')
        add(self.clauses)
        return 'WITH '+',\n\t'.join(encode(clause) for clause in clauses) + '\n'+encode(self.body)
        
class Select(Complex):
    def __init__(self, what, From=None, where=None):
        self.what = what
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

class Order(Complex):
    def __init__(self, clause, order):
        self.clause = clause
        self.order = order
    def sql(self):
        return encode(self.clause) + '\nORDER BY '+encode(self.order)

class Limit(Complex):
    def __init__(self, clause, limit, offset=None):
        self.clause = clause
        self.limit = limit
        self.offset = offset
    def sql(self):
        s = encode(self.clause) + '\nLIMIT '+encode(self.limit)
        if self.offset:
            s = s + " OFFSET "+encode(self.offset)
        return s

class BaseJoin(Complex):
    def __init__(self, operation, left, right, aux):
        self.operation = operation
        self.left = left
        self.right = right
        self.aux = aux
    def sql(self):
        s = encode((asGroup(self.left),self.operation,asGroup(self.right)))
        if self.aux is not None:
            s = s + ' ON '+encode(self.aux)
        return s

class InnerJoin(BaseJoin):
    def __init__(self, left, right, on):
        super(InnerJoin, self).__init__('INNER JOIN',left,right,on)

class OuterJoin(BaseJoin):
    def __init__(self, left, right, on):
        super(OuterJoin, self).__init__('LEFT OUTER JOIN',left,right,on)

class FullJoin(BaseJoin):
    def __init__(self, left, right):
        super(FullJoin, self).__init__('JOIN',left,right,None)

class Group(SQL):
    def __init__(self, clause):
        self.clause = clause
    def sql(self):
        clause = self.clause
        while isinstance(clause,Group):
            clause = clause.clause
        return '(' + encode(self.clause) + ')'

class Binary(Group):
    op = None
    def __init__(self, left, right):
        super(Binary, self).__init__((asGroup(left),self.op,asGroup(right)))

class Unary(Group):
    op = None
    def __init__(self,clause):
        super(Unary, self).__init__((self.op,asGroup(clause)))

def asGroup(clause):
    if isinstance(clause,Group):
        return clause
    if isinstance(clause,(list,tuple,set,Binary,Complex)):
        return Group(clause)
    return clause
        
class AND(Binary):
    op = 'AND'

class OR(Binary):
    op = 'OR'
        
class NOT(Unary):
    op = 'NOT'

class EQ(Binary):
    op = '='

class IS(Binary):
    op = 'IS'
    
class IN(Binary):
    op = 'IN'

class Plus(Binary):
    op = '+'

class Intersects(Binary):
    op = '&&'

class AS(Group):
    def __init__(self, clause, name):
        super().__init__(clause)
        self.name = name
    def sql(self):
        return super().sql() + ' AS ' + encode(self.name)

class ANY(Group):
    def sql(self):
        return 'ANY' + super().sql()

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
