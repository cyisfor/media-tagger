import sys,os
sys.path.append(os.path.expanduser("~/code/postgresql-python"))
import postgresql as pg
from contextlib import contextmanager
from itertools import count

from threading import local

ProgrammingError = pg.SQLError

db = local()
c = None

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
    password = None
reopen()

def setup(*stmts):
    c.execute("COMMIT")
    for stmt in stmts:
        try:
            c.execute(stmt)
        except ProgrammingError: pass
