import sys,os
sys.path.insert(0,os.path.expanduser("/extra/user/code/postgresql-python"))
import postgresql as pg
from contextlib import contextmanager
from itertools import count

from threading import local

ProgrammingError = pg.SQLError

db = local()
c = None

def retransaction(rollback=False): return pg.retransaction(c,rollback)
def transaction(): return pg.transaction(c)
def saved(): return pg.saved(c)

tempctr = count(1)

@contextmanager
def temporaryTable(c,columns,notSoTemp=False):
    name = "temptable{}".format(tempctr.__next__())
    if notSoTemp:
        prefix = "CREATE"
    else:
        prefix = "CREATE TEMPORARY"
    try:
        c.execute(prefix+" TABLE "+name+" ("+columns+")")
        yield name
    finally:
        c.execute("DROP TABLE "+name)

def reopen():
    global c
    try:
        with open("passwd") as inp:
            password = inp.read()
    except IOError:
        password = None
    c = pg.Connection(dbname='pics',port=5433,password=password)
    #c.verbose = True
    c.out = open('/tmp/db.log','at')
    password = None
reopen()

def setup(*stmts):
    #c.execute("COMMIT")
    for stmt in stmts:
        try:
            c.execute(stmt)
        except ProgrammingError as e:
            if c.verbose:
                sys.stdout.write(stmt)
                print('')
                sys.stdout.write(e.info['message'].decode('utf-8'))
                print('')

place = os.path.dirname(__file__)

# either returns {name=statement...} or [statement...] depending on file format...
def source(path,namedStatements=True):
    if namedStatements:
        stmts = {}
    else:
        stmts = []
    mode = 0
    value = []
    inQuote = False
    with open(os.path.join(place,path)) as inp:
        for line in inp:
            if line.lstrip().startswith('--'): continue
            line = line.rstrip()
            if not line: continue
            if '$$' in line: 
                inQuote = not inQuote
            if namedStatements and mode is 0:
                name = line
                mode = 1
            else:
                if not inQuote and line[-1]==';':
                    mode = 0
                    line = line[:-1]
                else:
                    mode = 1
                value.append(line)
                if mode is 0:
                    value = "\n".join(value)
                    if namedStatements:
                        stmts[name] = value
                    else:
                        stmts.append(value)
                    value = []
                    name = None
    return stmts
