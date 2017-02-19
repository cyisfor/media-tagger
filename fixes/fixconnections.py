import syspath
import db
c = db.c
import os

if os.path.exists("derpcounter"):
    with open("derpcounter") as inp:
        skip = int(inp.read())
else:
    skip = 0

total = c.execute("SELECT count(*) FROM (SELECT id FROM tags WHERE name LIKE '%:%' OFFSET $1) AS beep",(skip,))[0][0]
count = 0

def doit():
	global count
	c.execute("CREATE TABLE IF NOT EXISTS toconnect (a int, b int, dis boolean DEFAULT FALSE NOT NULL)");
	
	for row in c.execute("select id,name from tags where name LIKE '%:%' ORDER BY id DESC OFFSET $1",(skip,)):
		wholetag,wholename = row
		if wholename.startswith(':'): continue
		count += 1
		print(wholename.encode('utf-8'),count,total)
		cname,tname = wholename.split(':',1)
		category = c.execute("SELECT findTag($1)",(cname,))[0][0]
		tag = c.execute("SELECT findTag($1)",(tname,))[0][0]

		if False:
			c.execute("UPDATE tags SET complexity = 0 WHERE id = $1",(category,))
			c.execute("UPDATE tags SET complexity = 1 WHERE id = $1",(wholetag,))
			c.execute("UPDATE tags SET complexity = 1 WHERE id = $1",(tag,))
		if True:
			c.execute("INSERT INTO toconnect (a,b,dis) VALUES ($1,$2,TRUE)",(category,tag))
			c.execute("INSERT INTO toconnect (a,b,dis) VALUES ($1,$2,TRUE)",(tag,category))
			c.execute("INSERT INTO toconnect (a,b,dis) VALUES ($1,$2,TRUE)",(wholetag,category))
			c.execute("INSERT INTO toconnect (a,b) VALUES ($1,$2)",(tag,wholetag))
			c.execute("INSERT INTO toconnect (a,b) VALUES ($1,$2)",(category,wholetag))
		if count % 100 == 0:
			if count > 1000:
				c.execute("CREATE INDEX IF NOT EXISTS toconnect_a_dis  ON toconnect(a,dis)")
				c.execute("CREATE INDEX IF NOT EXISTS toconnect_a  ON toconnect(a)")
			print('boop')
			for a, in c.execute("SELECT DISTINCT a FROM toconnect"):
				print("reconnecting",a)
				c.execute("""
UPDATE things SET neighbors = array(SELECT unnest(neighbors) UNION SELECT b FROM toconnect WHERE a = $1 AND NOT dis EXCEPT SELECT b FROM toconnect WHERE a = $1 AND dis)
WHERE neighbors && array(SELECT b FROM toconnect WHERE a = $1 AND NOT dis EXCEPT SELECT b FROM toconnect WHERE a = $1 AND dis)
				""",(a,))
			c.execute("
			db.retransaction()
			with open("derpcounter","w") as out:
				out.write(str(skip+count))

with db.transaction():
	c.execute("LOCK TABLE things IN ACCESS EXCLUSIVE MODE")
	c.execute("ALTER TABLE things DISABLE TRIGGER ALL")
	try:
		doit()
	finally:
		c.execute("ALTER TABLE things ENABLE TRIGGER ALL")
		
