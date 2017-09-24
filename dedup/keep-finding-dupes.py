import db

while True:
	count = db.execute("SELECT findDupes($1)",(0.4,))[0][0]
	if count == 0:
		break
	print(count)
