import db,create

with db.transaction():
    for derp in db.execute("SELECT media.id FROM media LEFT OUTER JOIN images ON media.id = images.id WHERE images.id IS NULL AND media.type LIKE 'image/%' ORDER BY media.id"):
        print(hex(derp[0]))
        create.retryCreateImage(derp[0])        

print("zero height images...")
				
with db.transaction():
	for derp, in db.execute("SELECT id FROM images WHERE height = 0 AND width = 0 ORDER BY id"):
		print(hex(derp))
		create.retryCreateImage(derp)
												 
