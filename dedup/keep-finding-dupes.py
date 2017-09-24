import db

while True:
	done = True
	for id,dupes,elapsed in db.execute("SELECT * FROM findDupes($1,$2,$3)",
																		 (0.4,'20 seconds',1000)):
		print(id,dupes and len(dupes),elapsed)
		done = False
	if done: break
