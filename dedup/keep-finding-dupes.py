import db

while True:
	done = True
	for id,dupes,elapsed db.execute("SELECT findDupes($1,$2,$3)",
																	(0.4,'20 seconds',1000)):
		print(id,len(dupes),elapsed);
		done = False
	if done: break
