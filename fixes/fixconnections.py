import syspath
import db
c = db.c
import os

if os.path.exists("derpcounter"):
    with open("derpcounter") as inp:
        skip = int(inp.read())
else:
    skip = 4700+235

total = c.execute("SELECT count(*) FROM (SELECT id FROM tags WHERE name LIKE '%:%' OFFSET $1) AS beep",(skip,))[0][0]
count = 0

def doit():
	for row in c.execute("select id,name from tags where name LIKE '%:%' OFFSET $1",(skip,)):
		wholetag,wholename = row
		if wholename.startswith(':'): continue
		count += 1
		print(wholename.encode('utf-8'),count,total)
		cname,tname = wholename.split(':',1)
		category = c.execute("SELECT findTag($1)",(cname,))[0][0]
		tag = c.execute("SELECT findTag($1)",(tname,))[0][0]

		c.execute("SELECT disconnect($2,$1)",(category,tag))
		c.execute("SELECT disconnect($1,$2)",(category,tag))
		c.execute("SELECT disconnect($2,$1)",(category,wholetag))
		c.execute("SELECT connectone($2,$1)",(tag,wholetag))
		c.execute("SELECT connectmanytoone(ARRAY[$1,$2]::INTEGER[],$3::INTEGER)",
							(tag,category,wholetag))
		if count % 100 == 0:
			print('boop')
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
		
