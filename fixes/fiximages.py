import syspath
import db,create,note

with db.transaction():
    for derp in db.execute("SELECT media.id FROM media LEFT OUTER JOIN images ON media.id = images.id WHERE images.id IS NULL AND media.type LIKE 'image/%' ORDER BY media.id"):
        print(hex(derp[0]))
        create.retryCreateImage(derp[0])        

note("zero height images...")
import filedb
with db.transaction():
	for ident, in db.execute("SELECT id FROM images WHERE height = 0 AND width = 0 ORDER BY id"):
		print(hex(ident))
		medium = filedb.mediaPath(ident)
		image, type = create.openImage(medium)
		animated, width, height = image
		assert(width != 0)
		assert(height != 0)
		print(width,height)
		break
		db.execute("UPDATE images SET width = $2, height = $3 WHERE id = $1",(ident,width,height))
												 
