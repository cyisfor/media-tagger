import concur

import sqlparse

import sys,os
sys.path.insert(0,os.path.expanduser("/extra/user/code/postgresql-python"))
import postgresql as pg
from contextlib import contextmanager
from itertools import count

from threading import local

ProgrammingError = pg.SQLError

tempctr = count(1)

@threadify
class DBProxy:
    c = None
    @export
    def execute(self,*a,**kw):
        if not hasattr(self,'c'):
            reopen()
        return self.c.execute(*a,**kw)
    @export
    def retransaction(self,rollback=False):
        return pg.retransaction(self.c,rollback)
    def transaction(self):
        return pg.transaction(self.c)
    def saved(self):
        return pg.saved(self.c)
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
    
    def reopen(self):
        try:
            with open("passwd") as inp:
                password = inp.read()
        except IOError:
            password = None
        self.c = pg.Connection(dbname='pics',port=5433,password=password)
        self.c.verbose = False
        #self.c.out = open('/tmp/self.log','at')
        password = None
    reopen()
    
    def vsetup(self, *stmts):
        for stmt in stmts:
            execute(stmt)
    
    def setup(self, *stmts):
        #execute("COMMIT")
        for stmt in stmts:
            try:
                execute(stmt)
            except ProgrammingError as e:
                if self.c.verbose:
                    sys.stdout.write(stmt)
                    print('')
                    sys.stdout.write(e.info['message'].decode('utf-8'))
                    print('')
    
    place = os.path.dirname(__file__)
    
    # either returns {name=statement...} or [statement...] depending on file format...
    def source(self, path,namedStatements=True):
        with open(os.path.join(place,path)) as inp:
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

sys.modules[__name__] = DBProxy()
