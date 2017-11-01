import sys,os
sys.path.insert(0,os.path.expanduser("/home/code/postgresql-python"))
import postgresql as pg
c = pg.Connection(dbname='derp')

c.execute("BEGIN")
for i in range(30000):
	print(i);
	if i % 10000 == 0:
		c.execute("COMMIT")
		c.execute("BEGIN")
	c.execute("CREATE TABLE lotsatables.t"+str(i)+" AS SELECT unnest($1::int[]) AS boop",
						(tuple(range(i+1)[-10:]),));
	
c.execute("COMMIT")
