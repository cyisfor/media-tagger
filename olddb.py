import psycopg2
from contextlib import contextmanager
from progressbar import ProgressBar

ProgrammingError = psycopg2.ProgrammingError

@contextmanager
def derp(makeCursor):
    cursor = None
    try:
        cursor = makeCursor()
        cursor.execute("BEGIN")
        yield cursor
        cursor.execute("COMMIT")
    except:
        if cursor: cursor.execute("ROLLBACK")
        raise
    finally:
        if cursor is not None:
            cursor.close()

def cursor():
    return derp(c.cursor)

with open("passwd") as inp:
    password = inp.read()

c = psycopg2.connect("dbname=pics user=ion port=5433 password="+password)
password = None
