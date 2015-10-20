# this is probably a horrible idea

class SQL:
    def sql(self):
        raise NotImplementedError("This is some SQL statement.")

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

class Select(SQL):
    def __init__(self, what, From, where):
        self.what = what
        self.From = From
        self.where = where
    def sql(self):
        return 'SELECT '+', '.join(encode(arg) for arg in self.what) + '\nFROM '+encode(self.From)+'\nWHERE '+encode(self.where)

class Order(SQL):
    def __init__(self, clause, order):
        self.clause = clause
        self.order = order
    def sql(self):
        return encode(self.clause) + '\nORDER BY '+encode(self.order)

class Limit(SQL):
    def __init__(self, clause, limit, offset=None):
        self.clause = clause
        self.limit = limit
        self.offset = offset
    def sql(self):
        s = encode(self.clause) + '\nLIMIT '+encode(self.limit)
        if self.offset:
            s = s + " OFFSET "+encode(self.offset)
        return s

class BaseJoin(SQL):
    def __init__(self, operation, left, right, aux):
        self.operation = operation
        self.left = left
        self.right = right
        self.aux = aux
    def sql(self):
        s = encode((self.left,self.operation,self.right))
        if self.aux is not None:
            s = s + ' ON '+self.aux
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
        return '(' + self.clause + ')'

def asGroup(clause):
    if isinstance(clause,Group):
        return clause
    return Group(clause)
        
class Boolean(SQL):
    def __init__(self, op, left, right):
        self.op = op
        self.left = asGroup(left)
        self.right = asGroup(right)
    def sql(self):
        return encode(Group((self.left,self.op,self.right)))

class AND(Boolean):
    def __init__(self, left, right):
        super(AND, self).__init__('AND',left,right)

class OR(Boolean):
    def __init__(self, left, right):
        super(OR, self).__init__('OR',left,right)

class NOT(SQL):
    def __init__(self, clause):
        self.clause = clause
    def sql(self):
        return Group(('NOT',self.clause))

class EQ(Boolean):
    def __init__(self,left,right):
        super(EQ, self).__init__('=',left,right)

class IS(Boolean):
    def __init__(self,left,right):
        super(IS, self).__init__('IS',left,right)

class IS(Boolean):
    def __init__(self,left,right):
        super(IS, self).__init__('IS',left,right)

        
    
def main():
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
                AND(EQ("tableB.beep","$1"),EQ("tableA.foo","tableC.baz + 3")),
            "tableB.bar, tableC.baz"),
        "$2",
        20)
    print(stmt.sql())
    print('---')
    print(stmt.clause.clause.sql())

if __name__ == '__main__':
    main()
