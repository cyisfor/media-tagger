import db

while True:
	done = True
	rows = db.execute("SELECT * FROM findDupes($1,$2,$3)",
												 (0.4,'20 seconds',1000))
	count = len(rows)
	if count == 0: break
	print(count)
	for id,dupes,elapsed in rows:
		if dupes: print(hex(id),[hex(id) for id in dupes])


db.execute("SELECT * FROM findDupesDone()")
