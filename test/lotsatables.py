sys.path.insert(0,os.path.expanduser("/home/code/postgresql-python"))
import postgresql as pg
c = pg.Connection(dbname='derp')

for i in range(100000):
	c.execute("CREATE TABLE lotsatable.t"+str(i)+" AS SELECT unnest($1) AS boop",
						range(i+1));
	
