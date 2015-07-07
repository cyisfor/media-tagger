import sqlparse

import sys,os
sys.path.insert(0,os.path.expanduser("/extra/user/code/postgresql-python"))
import postgresql as pg
from contextlib import contextmanager
from itertools import count

from threading import local

ProgrammingError = pg.SQLError

db = local()

def execute(*a,**kw):
    if not hasattr(db,'c'):
        reopen()
    return db.c.execute(*a,**kw)

def retransaction(rollback=False): return pg.retransaction(db.c,rollback)
def transaction(): return pg.transaction(db.c)
def saved(): return pg.saved(db.c)

tempctr = count(1)

@contextmanager
def temporaryTable(columns,notSoTemp=False):
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

def reopen():
    try:
        with open("passwd") as inp:
            password = inp.read()
    except IOError:
        password = None
    db.c = pg.Connection(dbname='pics',port=5433,password=password)
    db.c.verbose = True
    db.c.out = open('/tmp/db.log','at')
    password = None
reopen()

def vsetup(*stmts):
    for stmt in stmts:
        execute(stmt)

def setup(*stmts):
    #execute("COMMIT")
    for stmt in stmts:
        try:
            execute(stmt)
        except ProgrammingError as e:
            if db.c.verbose:
                sys.stdout.write(stmt)
                print('')
                sys.stdout.write(e.info['message'].decode('utf-8'))
                print('')

place = os.path.dirname(__file__)

# either returns {name=statement...} or [statement...] depending on file format...
def source(path,namedStatements=True):
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
