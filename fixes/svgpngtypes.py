import db,create,filedb,derpmagic as magic

with db.transaction():
    for image,name in db.execute('''SELECT media.id,media.name FROM media 
    INNER JOIN images ON media.id = images.id 
    WHERE 
    media.type = $1 AND media.name LIKE $2''',('image/png','%.svg')):
        print(hex(image),name)
        source = filedb.mediaPath(image)
        print(source)
        info,type = create.openImage(source)
        if type == 'image/png': continue
        print(type)
        db.execute("UPDATE media SET type = $1 WHERE id = $2",(image,type))
        db.execute('COMMIT')
        db.execute('BEGIN')
